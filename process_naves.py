#!/usr/bin/env python3
"""
Process Nave's Topical Bible PDF for TinyOwl integration.
Extracts topical entries and prepares them for ChromaDB vectorization.
"""

import json
import re
from pathlib import Path
from pypdf import PdfReader
from typing import List, Dict, Any

def extract_naves_text(pdf_path: str) -> str:
    """Extract text from Nave's Topical Bible PDF."""
    print(f"📖 Extracting text from {pdf_path}...")

    reader = PdfReader(pdf_path)
    full_text = ""

    for page_num, page in enumerate(reader.pages):
        if page_num % 100 == 0:
            print(f"   Processing page {page_num + 1}/{len(reader.pages)}")

        text = page.extract_text()
        full_text += text + "\n"

    print(f"✅ Extracted {len(full_text):,} characters from {len(reader.pages)} pages")
    return full_text

def parse_topical_entries(text: str) -> List[Dict[str, Any]]:
    """Parse Nave's topical entries into structured chunks."""
    print("🔍 Parsing topical entries...")

    # Split into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    entries = []
    current_topic = None
    current_content = []
    current_scripture_refs = []

    # Pattern to detect main topics (usually all caps or bold-like)
    topic_pattern = re.compile(r'^[A-Z][A-Z\s&,\-\']{4,}\.?\s*$')

    # Pattern to detect scripture references
    scripture_pattern = re.compile(r'\b(?:[1-3]?\s*)?(?:Gen|Exo|Lev|Num|Deu|Jos|Jud|Rut|[1-2]?\s*Sam|[1-2]?\s*Kin|[1-2]?\s*Chr|Ezr|Neh|Est|Job|Psa|Pro|Ecc|Son|Isa|Jer|Lam|Eze|Dan|Hos|Joe|Amo|Oba|Jon|Mic|Nah|Hab|Zep|Hag|Zec|Mal|Mat|Mar|Luk|Joh|Act|Rom|[1-2]?\s*Cor|Gal|Eph|Phi|Col|[1-2]?\s*The|[1-2]?\s*Tim|Tit|Phl|Heb|Jam|[1-2]?\s*Pet|[1-3]?\s*Joh|Jud|Rev)\s*\d+:\d+', re.IGNORECASE)

    for line in lines:
        # Skip very short lines or page numbers
        if len(line) < 3 or line.isdigit():
            continue

        # Check if this is a new topic
        if topic_pattern.match(line) and len(line) > 10:
            # Save previous entry if it exists
            if current_topic and current_content:
                entries.append({
                    'topic': current_topic,
                    'content': ' '.join(current_content),
                    'scripture_references': current_scripture_refs,
                    'chunk_type': 'topical_entry',
                    'source': 'naves_topical_bible'
                })

            # Start new topic
            current_topic = line.strip().rstrip('.')
            current_content = []
            current_scripture_refs = []

        elif current_topic:  # We're inside a topic
            # Extract scripture references from this line
            refs = scripture_pattern.findall(line)
            current_scripture_refs.extend(refs)

            # Add content
            current_content.append(line)

    # Don't forget the last entry
    if current_topic and current_content:
        entries.append({
            'topic': current_topic,
            'content': ' '.join(current_content),
            'scripture_references': current_scripture_refs,
            'chunk_type': 'topical_entry',
            'source': 'naves_topical_bible'
        })

    print(f"✅ Parsed {len(entries)} topical entries")
    return entries

def create_naves_chunks(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create ChromaDB-ready chunks from Nave's entries."""
    print("📦 Creating ChromaDB chunks...")

    chunks = []

    for i, entry in enumerate(entries):
        # Create main topical chunk
        chunk_id = f"naves_topic_{i+1:05d}"

        # Construct document text for embedding
        doc_text = f"Topic: {entry['topic']}\n\n{entry['content']}"

        # Scripture references as searchable text
        if entry['scripture_references']:
            refs_text = ', '.join(set(entry['scripture_references']))  # Remove duplicates
            doc_text += f"\n\nScripture References: {refs_text}"

        chunk = {
            'id': chunk_id,
            'document': doc_text,
            'metadata': {
                'topic': entry['topic'],
                'chunk_type': entry['chunk_type'],
                'source': entry['source'],
                'scripture_count': len(set(entry['scripture_references'])),
                'content_length': len(entry['content'])
            }
        }

        chunks.append(chunk)

    print(f"✅ Created {len(chunks)} ChromaDB chunks")
    return chunks

def main():
    """Main processing function."""
    print("🦉 TinyOwl: Processing Nave's Topical Bible")
    print("=" * 50)

    # Paths
    pdf_path = Path.home() / "Downloads" / "Nave's Topical Bible..pdf"
    output_dir = Path("domains/theology/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract text
    text = extract_naves_text(str(pdf_path))

    # Save raw text
    raw_text_path = output_dir / "naves_topical_bible_raw.txt"
    with open(raw_text_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"💾 Saved raw text to {raw_text_path}")

    # Parse entries
    entries = parse_topical_entries(text)

    # Create chunks
    chunks = create_naves_chunks(entries)

    # Save chunks
    chunks_dir = Path("domains/theology/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_dir / "naves_topical_chunks.json"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved {len(chunks)} chunks to {chunks_path}")

    print("\n🎯 Nave's Topical Bible processing complete!")
    print(f"   📊 Total topics: {len(entries)}")
    print(f"   📦 Total chunks: {len(chunks)}")
    print(f"   📍 Ready for ChromaDB vectorization")

if __name__ == "__main__":
    main()