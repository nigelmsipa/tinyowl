#!/usr/bin/env python3
"""
Process Stephen Bohr Q&A Batch 6 (Q17-Q36, 20 pairs)
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

INPUT_FILE = RAW_DIR / "stephen_bohr_qa_formatted_06.md"
CHUNKS_OUTPUT = CHUNKS_DIR / "stephen_bohr_qa_06_chunks.json"
TRAINING_OUTPUT = TRAINING_DIR / "stephen_bohr_qa_06_training.jsonl"

# Ensure directories exist
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
TRAINING_DIR.mkdir(parents=True, exist_ok=True)


def parse_qa_pairs(content: str) -> List[Dict]:
    """Parse Q&A pairs from markdown content"""
    qa_pairs = []

    # Split by Q&A pair headers
    pair_pattern = r'## Q&A Pair (\d+)\n\n\*\*QUESTION:\*\*\n\n(.*?)\n\n\*\*ANSWER:\*\*\n\n(.*?)(?=\n---\n\n## Q&A Pair|\n---\n\n## END|\Z)'

    matches = re.findall(pair_pattern, content, re.DOTALL)

    for pair_num, question, answer in matches:
        qa_pairs.append({
            "pair_num": int(pair_num),
            "question": question.strip(),
            "answer": answer.strip()
        })

    print(f"Found {len(qa_pairs)} Q&A pairs")
    return qa_pairs


def extract_topic(answer: str) -> str:
    """Extract main topic from answer (first sentence)"""
    first_sentence = answer.split('.')[0]
    return first_sentence[:100] if len(first_sentence) > 100 else first_sentence


def chunk_for_retrieval(qa_pairs: List[Dict]) -> List[Dict]:
    """Create chunks optimized for RAG retrieval"""
    chunks = []

    for qa in qa_pairs:
        pair_num = qa["pair_num"]
        question = qa["question"]
        answer = qa["answer"]

        main_topic = extract_topic(answer)

        # Chunk 1: Full Q&A
        chunks.append({
            "id": f"stephen_bohr_qa_06_{pair_num:03d}_full",
            "text": f"Question: {question}\n\nAnswer: {answer}",
            "source": "stephen_bohr_qa_06",
            "pair_num": pair_num,
            "chunk_type": "qa_full",
            "main_topic": main_topic
        })

        # Chunk 2: Question-focused (for semantic search)
        chunks.append({
            "id": f"stephen_bohr_qa_06_{pair_num:03d}_question",
            "text": f"Question: {question}\n\nBrief answer: {answer[:300]}...",
            "source": "stephen_bohr_qa_06",
            "pair_num": pair_num,
            "chunk_type": "qa_brief",
            "main_topic": main_topic
        })

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
    print("Processing Stephen Bohr Q&A Batch 06...")

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
