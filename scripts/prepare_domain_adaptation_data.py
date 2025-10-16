#!/usr/bin/env python3
"""
Prepare domain adaptation dataset from all TinyOwl chunks.

This script extracts all 403K chunks and formats them for Phase 1 fine-tuning
(domain adaptation) where TinyLlama learns theological knowledge.

Output format: Simple text, one chunk per line (JSONL format for training)
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import sys

# Chunk files to process
CHUNK_FILES = [
    # Bible translations
    "domains/theology/chunks/kjv_verses_chunks.json",
    "domains/theology/chunks/kjv_pericopes_chunks.json",
    "domains/theology/chunks/kjv_chapters_chunks.json",
    "domains/theology/chunks/web_verses_chunks.json",
    "domains/theology/chunks/web_pericopes_chunks.json",
    "domains/theology/chunks/web_chapters_chunks.json",

    # Strong's concordance
    "domains/theology/chunks/strongs_concordance_entries_chunks.json",
    "domains/theology/chunks/strongs_strongs_numbers_chunks_with_defs.json",
    "domains/theology/chunks/strongs_word_summaries_chunks.json",

    # Spirit of Prophecy
    "domains/theology/chunks/sop_paragraphs.json",
    "domains/theology/chunks/sop_chapters.json",

    # Nave's Topical Bible (all collections)
    "domains/theology/chunks/naves_scripture_entries.json",
    "domains/theology/chunks/naves_topic_entries.json",
    "domains/theology/chunks/naves_topic_sections.json",
    "domains/theology/chunks/naves_complete_topics.json",

    # Sermons - Amazing Facts
    "domains/theology/chunks/amazing_paragraphs.json",
    "domains/theology/chunks/amazing_chapters.json",

    # Sermons - Secrets Unsealed
    "domains/theology/chunks/secrets_unsealed_paragraphs.json",
    "domains/theology/chunks/secrets_unsealed_chapters.json",

    # Sermons - Total Onslaught (Walter Veith)
    "domains/theology/chunks/total_onslaught_paragraphs.json",
    "domains/theology/chunks/total_onslaught_lectures.json",

    # Sermons - 3ABN
    "domains/theology/chunks/threeabn_paragraphs.json",
    "domains/theology/chunks/threeabn_chapters.json",
]

def extract_chunks_from_file(filepath: Path) -> List[str]:
    """Extract text content from chunk file"""
    chunks = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, dict) and "chunks" in data:
            chunk_list = data["chunks"]
        elif isinstance(data, list):
            chunk_list = data
        else:
            print(f"⚠️  Unknown format in {filepath.name}")
            return chunks

        for chunk in chunk_list:
            # Handle both string chunks and object chunks
            if isinstance(chunk, str):
                # Simple string chunk (e.g., SOP paragraphs)
                text = chunk
                metadata = {}
            else:
                # Object chunk with metadata
                text = chunk.get("content") or chunk.get("text") or ""
                metadata = chunk.get("metadata", {})

            if text and len(text.strip()) > 20:  # Skip very short chunks
                # Format with source context
                source = metadata.get("source_id", "")
                book = metadata.get("book_id", "")
                chapter = metadata.get("chapter", "")

                if book and chapter:
                    formatted = f"{book} {chapter}: {text}"
                elif source:
                    formatted = f"[{source}] {text}"
                else:
                    formatted = text

                chunks.append(formatted.strip())

        print(f"✅ {filepath.name}: {len(chunks):,} chunks")

    except Exception as e:
        print(f"❌ Error processing {filepath.name}: {e}")

    return chunks


def prepare_domain_adaptation_dataset():
    """Prepare complete domain adaptation dataset"""

    print("🦉 TinyOwl Domain Adaptation Dataset Preparation")
    print("=" * 60)
    print()

    root = Path("/home/nigel/tinyowl")
    output_file = root / "training_data" / "domain_adaptation.jsonl"
    output_file.parent.mkdir(exist_ok=True)

    all_chunks = []

    # Process each chunk file
    for chunk_file in CHUNK_FILES:
        filepath = root / chunk_file
        if filepath.exists():
            chunks = extract_chunks_from_file(filepath)
            all_chunks.extend(chunks)
        else:
            print(f"⚠️  Not found: {chunk_file}")

    print()
    print(f"📊 Total chunks extracted: {len(all_chunks):,}")

    # Write in JSONL format for training
    print(f"💾 Writing to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            # Simple format: one text per line
            entry = {"text": chunk}
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"✅ Domain adaptation dataset ready: {output_file}")
    print(f"📁 File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("Next step: Generate Q&A pairs from these chunks")


if __name__ == "__main__":
    prepare_domain_adaptation_dataset()
