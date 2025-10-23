#!/usr/bin/env python3
"""
Process Stephen Bohr Q&A Pair 4 (detailed markdown format)
Creates chunks for RAG retrieval AND JSONL training data
"""

import json
import re
from pathlib import Path
from typing import List, Dict

# Paths
RAW_DIR = Path("/home/nigel/tinyowl/domains/theology/raw")
CHUNKS_DIR = Path("/home/nigel/tinyowl/domains/theology/chunks")
TRAINING_DIR = Path("/home/nigel/tinyowl/domains/theology/training")

INPUT_FILE = RAW_DIR / "stephen_bohr_qa_formatted_04.md"
CHUNKS_OUTPUT = CHUNKS_DIR / "stephen_bohr_qa_04_chunks.json"
TRAINING_OUTPUT = TRAINING_DIR / "stephen_bohr_qa_04_training.jsonl"

# Ensure directories exist
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
TRAINING_DIR.mkdir(parents=True, exist_ok=True)


def parse_qa_pairs(content: str) -> List[Dict]:
    """Parse Q&A pairs from markdown content"""
    qa_pairs = []

    # Split by Q&A pair headers
    pair_pattern = r'## Q&A Pair (\d+)\n\n\*\*QUESTION:\*\*\n(.*?)\n\n\*\*ANSWER:\*\*\n\n(.*?)(?=\n---\n\n## Q&A Pair|\Z)'

    matches = re.findall(pair_pattern, content, re.DOTALL)

    for pair_num, question, answer in matches:
        qa_pairs.append({
            "pair_num": int(pair_num),
            "question": question.strip(),
            "answer": answer.strip()
        })

    print(f"Found {len(qa_pairs)} Q&A pairs")
    return qa_pairs


def chunk_for_retrieval(qa_pairs: List[Dict]) -> List[Dict]:
    """Create chunks optimized for RAG retrieval"""
    chunks = []

    for qa in qa_pairs:
        pair_num = qa["pair_num"]
        question = qa["question"]
        answer = qa["answer"]

        # Extract topics from answer (look for bold headers)
        topics = re.findall(r'\*\*(.*?)\*\*', answer[:500])
        main_topic = topics[0] if topics else "General Theology"

        # Chunk the answer by sections (identified by bold headers)
        sections = re.split(r'\n\*\*([^*]+)\*\*\n', answer)

        # First chunk: Full question + answer summary
        chunks.append({
            "id": f"stephen_bohr_qa_04_{pair_num:03d}_full",
            "text": f"Question: {question}\n\nAnswer: {answer[:1000]}...",
            "source": "stephen_bohr_qa_04",
            "pair_num": pair_num,
            "chunk_type": "qa_summary",
            "main_topic": main_topic
        })

        # Subsequent chunks: Question + each answer section
        chunk_index = 1
        for i in range(1, len(sections), 2):
            if i < len(sections):
                section_header = sections[i].strip()
                section_content = sections[i+1].strip() if i+1 < len(sections) else ""

                if section_content:
                    chunks.append({
                        "id": f"stephen_bohr_qa_04_{pair_num:03d}_chunk_{chunk_index:02d}",
                        "text": f"Question: {question}\n\n{section_header}:\n{section_content}",
                        "source": "stephen_bohr_qa_04",
                        "pair_num": pair_num,
                        "chunk_type": "qa_section",
                        "section": section_header,
                        "main_topic": main_topic
                    })
                    chunk_index += 1

    print(f"Created {len(chunks)} retrieval chunks")
    return chunks


def create_training_data(qa_pairs: List[Dict]) -> List[Dict]:
    """Create JSONL format for LLM fine-tuning"""
    training_data = []

    for qa in qa_pairs:
        # Format: {"instruction": "...", "input": "", "output": "..."}
        training_data.append({
            "instruction": qa["question"],
            "input": "",
            "output": qa["answer"]
        })

    print(f"Created {len(training_data)} training examples")
    return training_data


def main():
    print("Processing Stephen Bohr Q&A Formatted 04...")

    # Read input file
    print(f"Reading: {INPUT_FILE}")
    content = INPUT_FILE.read_text()

    # Parse Q&A pairs
    qa_pairs = parse_qa_pairs(content)

    if not qa_pairs:
        print("ERROR: No Q&A pairs found!")
        return

    # Create retrieval chunks
    print("\n--- Creating Retrieval Chunks ---")
    chunks = chunk_for_retrieval(qa_pairs)

    # Save chunks
    with open(CHUNKS_OUTPUT, 'w') as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved {len(chunks)} chunks to: {CHUNKS_OUTPUT}")

    # Create training data
    print("\n--- Creating Training Data ---")
    training_data = create_training_data(qa_pairs)

    # Save training data (JSONL format - one JSON object per line)
    with open(TRAINING_OUTPUT, 'w') as f:
        for item in training_data:
            f.write(json.dumps(item) + '\n')
    print(f"Saved {len(training_data)} training examples to: {TRAINING_OUTPUT}")

    # Statistics
    print("\n--- Summary ---")
    print(f"Input: {INPUT_FILE.name}")
    print(f"Q&A Pairs: {len(qa_pairs)}")
    print(f"Retrieval Chunks: {len(chunks)}")
    print(f"Training Examples: {len(training_data)}")
    print(f"\nOutputs:")
    print(f"  Chunks: {CHUNKS_OUTPUT}")
    print(f"  Training: {TRAINING_OUTPUT}")


if __name__ == "__main__":
    main()
