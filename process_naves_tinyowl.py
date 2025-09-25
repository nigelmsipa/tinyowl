#!/usr/bin/env python3
"""
TinyOwl: Add Nave's Topical Bible using proven hierarchical architecture
Follows the same pattern as Bible + Strong's concordance integration
"""

import json
import re
import chromadb
from pathlib import Path
from pypdf import PdfReader
from typing import List, Dict, Any
from chromadb.utils import embedding_functions

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

def parse_topics_hierarchically(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse Nave's using TinyOwl's hierarchical approach."""
    print("🏗️ Applying TinyOwl hierarchical chunking strategy...")

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Pattern to detect main topics (usually all caps)
    topic_pattern = re.compile(r'^[A-Z][A-Z\s&,\-\']{4,}\.?\s*$')

    # Scripture reference patterns
    scripture_pattern = re.compile(r'\b(?:Gen|Exo|Lev|Num|Deu|Jos|Jud|Rut|[1-2]?\s*Sam|[1-2]?\s*Kin|[1-2]?\s*Chr|Ezr|Neh|Est|Job|Psa|Pro|Ecc|Son|Isa|Jer|Lam|Eze|Dan|Hos|Joe|Amo|Oba|Jon|Mic|Nah|Hab|Zep|Hag|Zec|Mal|Mat|Mar|Luk|Joh|Act|Rom|[1-2]?\s*Cor|Gal|Eph|Phi|Col|[1-2]?\s*The|[1-2]?\s*Tim|Tit|Phl|Heb|Jam|[1-2]?\s*Pet|[1-3]?\s*Joh|Jud|Rev)\s*\d+:\d+')

    # Three hierarchical layers following TinyOwl pattern
    layers = {
        'topic_entries': [],     # Layer 1: Individual scripture entries (like verses)
        'topic_sections': [],    # Layer 2: Topic sections (like pericopes)
        'complete_topics': []    # Layer 3: Complete topics (like chapters)
    }

    topics = []
    current_topic = None
    current_content = []

    # First pass: Extract topics
    for line in lines:
        if len(line) < 3 or line.isdigit():
            continue

        if topic_pattern.match(line) and len(line) > 10:
            # Save previous topic
            if current_topic and current_content:
                topics.append({
                    'name': current_topic,
                    'content': '\n'.join(current_content)
                })

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

    print(f"✅ Parsed {len(topics)} main topics")

    # Second pass: Create hierarchical chunks following TinyOwl pattern
    for topic_idx, topic in enumerate(topics):
        topic_name = topic['name']
        content = topic['content']

        # Layer 3: Complete Topics (like KJV chapters)
        if len(content) <= 8000:  # Keep complete if reasonable size
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

        # Layer 2: Topic Sections (like pericopes)
        sections = split_into_sections(content, topic_name)
        for sect_idx, section in enumerate(sections):
            if len(section) > 200:
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

        # Layer 1: Scripture Entries (like verses)
        scripture_entries = extract_scripture_entries(content, topic_name)
        for entry_idx, entry in enumerate(scripture_entries):
            layers['topic_entries'].append({
                'id': f'naves_entry_{topic_idx+1:04d}_{entry_idx+1:03d}',
                'document': f"Topic: {topic_name}\n{entry['reference']}: {entry['text']}",
                'metadata': {
                    'topic': topic_name,
                    'layer': 'topic_entry',
                    'source': 'naves_topical_bible',
                    'topic_index': topic_idx + 1,
                    'entry_index': entry_idx + 1,
                    'scripture_reference': entry['reference'],
                    'content_length': len(entry['text'])
                }
            })

    # Print statistics like TinyOwl does
    print(f"\n📊 TinyOwl Hierarchical Results:")
    print(f"   Layer 1 (Topic Entries): {len(layers['topic_entries']):,} chunks")
    print(f"   Layer 2 (Topic Sections): {len(layers['topic_sections']):,} chunks")
    print(f"   Layer 3 (Complete Topics): {len(layers['complete_topics']):,} chunks")
    print(f"   🎯 Total: {sum(len(layer) for layer in layers.values()):,} chunks")

    return layers

def split_into_sections(content: str, topic_name: str) -> List[str]:
    """Split content into logical sections (pericope-like)."""
    if len(content) <= 2000:
        return [content]

    sections = []
    current_section = []
    lines = content.split('\n')

    for line in lines:
        current_section.append(line)

        # Split on natural breaks
        if (len('\n'.join(current_section)) > 1500 and
            (line.strip() == '' or
             re.match(r'^\s*[-–]\s*', line) or
             'See also' in line or
             re.search(r'[A-Z]{3,}', line))):  # Another topic reference

            if current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = []

    if current_section:
        sections.append('\n'.join(current_section).strip())

    return [s for s in sections if len(s.strip()) > 100]

def extract_scripture_entries(content: str, topic_name: str) -> List[Dict[str, str]]:
    """Extract individual scripture entries (verse-like chunks)."""
    entries = []

    # Look for scripture patterns with context
    lines = content.split('\n')
    for line in lines:
        # Find scripture references
        refs = re.findall(r'([A-Za-z0-9]+\s*\d+:\d+(?:-\d+)?)', line)
        if refs and len(line.strip()) > 20:
            for ref in refs:
                entries.append({
                    'reference': ref,
                    'text': line.strip()
                })

    return entries[:50]  # Limit to avoid explosion

def add_to_chromadb(layers: Dict[str, List[Dict[str, Any]]]):
    """Add to ChromaDB using BGE-large embeddings (matching TinyOwl)."""
    print("🗃️ Adding to ChromaDB with BGE-large embeddings...")

    # Use same embedding function as existing TinyOwl system
    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name='BAAI/bge-large-en-v1.5'
    )

    client = chromadb.PersistentClient(path='./chat_app/vectordb')

    for layer_name, chunks in layers.items():
        if not chunks:
            continue

        collection_name = f"naves_{layer_name}"
        print(f"\n📦 Processing {collection_name}...")

        # Create collection (or recreate if exists)
        try:
            existing = client.get_collection(collection_name)
            client.delete_collection(collection_name)
            print(f"  🔄 Recreated collection (was {existing.count():,} items)")
        except:
            pass

        collection = client.create_collection(
            name=collection_name,
            embedding_function=bge_ef,
            metadata={"description": f"Nave's Topical Bible - {layer_name}"}
        )

        # Add in batches (following TinyOwl pattern)
        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            batch_num = (i // batch_size) + 1

            # Prepare batch data
            batch_chunks = chunks[i:batch_end]
            ids = [chunk['id'] for chunk in batch_chunks]
            documents = [chunk['document'] for chunk in batch_chunks]
            metadatas = [chunk['metadata'] for chunk in batch_chunks]

            try:
                collection.add(ids=ids, documents=documents, metadatas=metadatas)

                if batch_num % 5 == 0 or batch_num == total_batches:
                    print(f"    Batch {batch_num}/{total_batches} complete")

            except Exception as e:
                print(f"    ❌ Error in batch {batch_num}: {e}")
                continue

        final_count = collection.count()
        print(f"  ✅ {collection_name}: {final_count:,} chunks embedded")

def main():
    """Process Nave's using TinyOwl architecture."""
    print("🦉 TinyOwl: Adding Nave's Topical Bible")
    print("=" * 50)

    # Extract from PDF
    pdf_path = Path.home() / "Downloads" / "Nave's Topical Bible..pdf"
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    text = extract_naves_text(str(pdf_path))

    # Create hierarchical chunks
    hierarchical_chunks = parse_topics_hierarchically(text)

    # Save JSON files (following TinyOwl pattern)
    output_dir = Path("domains/theology/chunks")
    output_dir.mkdir(parents=True, exist_ok=True)

    for layer_name, chunks in hierarchical_chunks.items():
        output_path = output_dir / f"naves_{layer_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(chunks):,} {layer_name} to {output_path}")

    # Add to ChromaDB
    add_to_chromadb(hierarchical_chunks)

    total_chunks = sum(len(chunks) for chunks in hierarchical_chunks.values())
    print(f"\n🎯 Nave's Topical Bible integration complete!")
    print(f"   📊 Added {total_chunks:,} chunks to TinyOwl database")
    print(f"   💬 Ready for #topic hotkeys in chat interface")

if __name__ == "__main__":
    main()