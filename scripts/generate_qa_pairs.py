#!/usr/bin/env python3
"""
Generate Q&A pairs from TinyOwl chunks for instruction tuning.

Uses AI (Claude/GPT) to generate 2-3 questions per chunk that the chunk would answer.
This creates training data for Phase 2 (instruction tuning).

Output: JSONL file with instruction-input-output format
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import time

# Choose your AI provider
USE_ANTHROPIC = False  # Set to True to use Anthropic instead (cheaper)


def generate_questions_for_chunk(chunk_text: str, metadata: Dict, client) -> List[str]:
    """Generate 2-3 questions that this chunk would answer"""

    # Create a prompt that generates relevant questions
    prompt = f"""Given this theological text, generate 2-3 natural questions that someone might ask that this text would answer.

Text: {chunk_text[:500]}

Generate questions that are:
- Specific to the content
- Natural (how people actually ask)
- Answerable from the text
- Theologically appropriate

Return ONLY the questions, one per line, no numbering."""

    try:
        if USE_ANTHROPIC:
            # Anthropic Claude
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Cheap and fast
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            questions_text = response.content[0].text
        else:
            # OpenAI GPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            questions_text = response.choices[0].message.content

        # Parse questions (one per line)
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and '?' in q]
        return questions[:3]  # Max 3 questions

    except Exception as e:
        print(f"  ⚠️  Error generating questions: {e}")
        return []


def load_chunks_sample(limit: int = None) -> List[Dict[str, Any]]:
    """Load a sample of chunks for Q&A generation"""

    root = Path("/home/nigel/tinyowl")

    # Priority files for Q&A generation (most important content)
    priority_files = [
        "domains/theology/chunks/kjv_verses_chunks.json",  # Sample of Bible verses
        "domains/theology/chunks/sop_paragraphs.json",  # Spirit of Prophecy
        "domains/theology/chunks/strongs_concordance_entries_chunks.json",  # Strong's
    ]

    chunks = []

    for chunk_file in priority_files:
        filepath = root / chunk_file

        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunk_list = data.get("chunks", []) if isinstance(data, dict) else data

        # Sample from each file
        sample_size = min(len(chunk_list), 10000)  # 10K from each
        for chunk in chunk_list[:sample_size]:
            text = chunk.get("content") or chunk.get("text", "")
            if text and len(text.strip()) > 50:
                chunks.append({
                    "text": text,
                    "metadata": chunk.get("metadata", {})
                })

        if limit and len(chunks) >= limit:
            break

    return chunks[:limit] if limit else chunks


def generate_qa_dataset(max_chunks: int = 30000):
    """Generate Q&A pairs for instruction tuning"""

    print("🦉 TinyOwl Q&A Pair Generation")
    print("=" * 60)
    print()

    # Initialize AI client
    if USE_ANTHROPIC:
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("❌ ANTHROPIC_API_KEY not set")
                return
            client = Anthropic(api_key=api_key)
            print("✅ Using Claude (Anthropic)")
        except ImportError:
            print("❌ Install: pip install anthropic")
            return
    else:
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ OPENAI_API_KEY not set")
                return
            client = OpenAI(api_key=api_key)
            print("✅ Using GPT (OpenAI)")
        except ImportError:
            print("❌ Install: pip install openai")
            return

    print()

    # Load chunks
    print(f"📚 Loading chunks (max {max_chunks:,})...")
    chunks = load_chunks_sample(limit=max_chunks)
    print(f"✅ Loaded {len(chunks):,} chunks")
    print()

    # Prepare output
    output_file = Path("/home/nigel/tinyowl/training_data/instruction_tuning.jsonl")
    output_file.parent.mkdir(exist_ok=True)

    qa_pairs = []
    processed = 0
    skipped = 0

    print("🔄 Generating Q&A pairs...")
    print("(This will take a while - ~2-3 chunks per second)")
    print()

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            # Generate questions
            questions = generate_questions_for_chunk(chunk["text"], chunk["metadata"], client)

            if not questions:
                skipped += 1
                continue

            # Create training examples
            for question in questions:
                qa_pair = {
                    "instruction": question,
                    "input": "",  # No additional input needed
                    "output": chunk["text"]
                }

                f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
                qa_pairs.append(qa_pair)

            processed += 1

            # Progress update
            if (i + 1) % 100 == 0:
                print(f"  Processed: {processed:,} chunks → {len(qa_pairs):,} Q&A pairs (skipped {skipped})")

            # Rate limiting (avoid API throttling)
            time.sleep(0.1)  # 10 requests/second

    print()
    print(f"✅ Q&A generation complete!")
    print(f"📊 Processed: {processed:,} chunks")
    print(f"📊 Generated: {len(qa_pairs):,} Q&A pairs")
    print(f"📁 Output: {output_file}")
    print(f"💰 Estimated cost: ${len(chunks) * 0.0005:.2f}")  # Rough estimate
    print()
    print("Next step: Fine-tune TinyLlama with both datasets")


if __name__ == "__main__":
    # Start with 5000 chunks for testing, then scale up
    generate_qa_dataset(max_chunks=5000)
