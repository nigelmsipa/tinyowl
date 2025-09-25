#!/usr/bin/env python3
"""
TinyOwl Hierarchical Chunking for Nave's Topical Bible.
Implements 3-layer strategy: Scripture Entries -> Topic Sections -> Complete Topics
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

def create_hierarchical_naves_chunks(raw_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Create hierarchical chunks using TinyOwl's proven 3-layer strategy."""
    print("🏗️ Implementing TinyOwl hierarchical chunking strategy...")

    # Split into topics first
    topics = parse_raw_topics(raw_text)

    layers = {
        'scripture_entries': [],  # Layer 1: Individual scripture references
        'topic_sections': [],     # Layer 2: Logical topic sections
        'complete_topics': []     # Layer 3: Complete topics (size-capped)
    }

    for topic_idx, topic_data in enumerate(topics):
        topic_name = topic_data['name']
        content = topic_data['content']

        print(f"   Processing topic {topic_idx+1}/{len(topics)}: {topic_name}")

        # Layer 3: Complete Topic (size-capped)
        if len(content) <= 10000:  # Keep complete if reasonable size
            layers['complete_topics'].append({
                'id': f'naves_topic_{topic_idx+1:04d}',
                'document': f"Topic: {topic_name}\n\n{content}",
                'metadata': {
                    'topic': topic_name,
                    'layer': 'complete_topic',
                    'source': 'naves_topical_bible',
                    'topic_index': topic_idx + 1,
                    'content_length': len(content)
                }
            })

        # Layer 2: Topic Sections (for large topics)
        sections = split_topic_into_sections(content, topic_name)
        for sect_idx, section in enumerate(sections):
            if len(section) > 200:  # Only create section if substantial
                layers['topic_sections'].append({
                    'id': f'naves_section_{topic_idx+1:04d}_{sect_idx+1:02d}',
                    'document': f"Topic: {topic_name} (Section {sect_idx+1})\n\n{section}",
                    'metadata': {
                        'topic': topic_name,
                        'layer': 'topic_section',
                        'source': 'naves_topical_bible',
                        'topic_index': topic_idx + 1,
                        'section_index': sect_idx + 1,
                        'content_length': len(section)
                    }
                })

        # Layer 1: Scripture Entries (fine granularity)
        scripture_entries = extract_scripture_entries(content, topic_name)
        for entry_idx, entry in enumerate(scripture_entries):
            layers['scripture_entries'].append({
                'id': f'naves_entry_{topic_idx+1:04d}_{entry_idx+1:03d}',
                'document': f"Topic: {topic_name}\nScripture: {entry['reference']}\n\n{entry['text']}",
                'metadata': {
                    'topic': topic_name,
                    'layer': 'scripture_entry',
                    'source': 'naves_topical_bible',
                    'topic_index': topic_idx + 1,
                    'entry_index': entry_idx + 1,
                    'scripture_reference': entry['reference'],
                    'content_length': len(entry['text'])
                }
            })

    # Print statistics
    print(f"\n📊 Hierarchical Chunking Results:")
    print(f"   Layer 1 (Scripture Entries): {len(layers['scripture_entries']):,} chunks")
    print(f"   Layer 2 (Topic Sections): {len(layers['topic_sections']):,} chunks")
    print(f"   Layer 3 (Complete Topics): {len(layers['complete_topics']):,} chunks")
    print(f"   🎯 Total: {sum(len(layer) for layer in layers.values()):,} chunks")

    return layers

def parse_raw_topics(text: str) -> List[Dict[str, Any]]:
    """Parse raw text into topic structures."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    topics = []
    current_topic = None
    current_content = []

    # Improved topic detection
    topic_pattern = re.compile(r'^[A-Z][A-Z\s&,\-\'\(\)]{4,}\.?\s*$')

    for line in lines:
        if len(line) < 3 or line.isdigit():
            continue

        # Check for new topic
        if topic_pattern.match(line) and len(line) > 10:
            # Save previous topic
            if current_topic and current_content:
                topics.append({
                    'name': current_topic,
                    'content': '\n'.join(current_content)
                })

            # Start new topic
            current_topic = line.strip().rstrip('.')
            current_content = []
        elif current_topic:
            current_content.append(line)

    # Don't forget last topic
    if current_topic and current_content:
        topics.append({
            'name': current_topic,
            'content': '\n'.join(current_content)
        })

    return topics

def split_topic_into_sections(content: str, topic_name: str) -> List[str]:
    """Split large topics into logical sections."""
    # For very large content, split into sections
    if len(content) <= 3000:
        return [content]  # Small enough, keep as one section

    # Split by natural breaks (double newlines, scripture patterns, etc.)
    sections = []
    current_section = []

    lines = content.split('\n')

    for line in lines:
        current_section.append(line)

        # Split criteria: sections getting long + natural break
        if (len('\n'.join(current_section)) > 2000 and
            (line.strip() == '' or  # Empty line
             re.match(r'^\s*[-–]\s*', line) or  # Dash-prefixed items
             re.search(r'See [A-Z]', line))):  # Cross-references

            if current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = []

    # Add remaining content
    if current_section:
        sections.append('\n'.join(current_section).strip())

    return [s for s in sections if len(s.strip()) > 100]

def extract_scripture_entries(content: str, topic_name: str) -> List[Dict[str, str]]:
    """Extract individual scripture entries for fine-grained search."""
    entries = []

    # Pattern for scripture references
    scripture_pattern = re.compile(
        r'–([^–\n]+(?:(?:Ge|Ex|Le|Nu|De|Jos|Jud|Ru|1Sa|2Sa|1Ki|2Ki|1Ch|2Ch|Ezr|Ne|Es|Job|Ps|Pr|Ec|Song|Isa|Jer|La|Eze|Da|Ho|Joe|Am|Ob|Jon|Mic|Na|Hab|Zep|Hag|Zec|Mal|Mt|Mr|Lu|Joh|Ac|Ro|1Co|2Co|Ga|Eph|Php|Col|1Th|2Th|1Ti|2Ti|Tit|Phm|Heb|Jas|1Pe|2Pe|1Jo|2Jo|3Jo|Jude|Re)\s*\d+:\d+[^–\n]*)+)',
        re.IGNORECASE
    )

    for match in scripture_pattern.finditer(content):
        entry_text = match.group(1).strip()

        # Extract scripture reference
        ref_match = re.search(r'([A-Za-z0-9]+\s*\d+:\d+(?:-\d+)?)', entry_text)
        reference = ref_match.group(1) if ref_match else 'Unknown'

        if len(entry_text) > 20:  # Only meaningful entries
            entries.append({
                'reference': reference,
                'text': entry_text
            })

    return entries

def main():
    """Main processing with hierarchical chunking."""
    print("🦉 TinyOwl: Hierarchical Processing of Nave's Topical Bible")
    print("=" * 60)

    # Load raw text
    raw_text_path = Path("domains/theology/raw/naves_topical_bible_raw.txt")
    if not raw_text_path.exists():
        print("❌ Raw text file not found. Run process_naves.py first.")
        return

    with open(raw_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Create hierarchical chunks
    hierarchical_chunks = create_hierarchical_naves_chunks(raw_text)

    # Save each layer separately
    chunks_dir = Path("domains/theology/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)

    for layer_name, chunks in hierarchical_chunks.items():
        output_path = chunks_dir / f"naves_{layer_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(chunks):,} {layer_name} to {output_path}")

    # Create combined file for easy loading
    all_chunks = []
    for chunks in hierarchical_chunks.values():
        all_chunks.extend(chunks)

    combined_path = chunks_dir / "naves_hierarchical_all.json"
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved {len(all_chunks):,} total chunks to {combined_path}")

    print(f"\n🎯 TinyOwl Hierarchical Chunking Complete!")
    print(f"   Ready for ChromaDB vectorization with BGE-large embeddings")

if __name__ == "__main__":
    main()