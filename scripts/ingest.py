#!/usr/bin/env python3
"""
TinyOwl Ingestion Script

This script handles the complete ingestion pipeline:
1. PDF text extraction
2. Text cleaning and processing
3. Chunking based on configured strategies
4. Vector embedding generation
5. Storage in ChromaDB

Usage:
    python ingest.py --config configs/sources.yaml --domain theology
"""

import os
import sys
import argparse
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import chromadb
from pypdf import PdfReader
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("tinyowl-ingest")

# Define base paths
BASE_DIR = Path(__file__).parent.parent.absolute()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from PDF with metadata
    
    Returns:
        List of pages with text and metadata
    """
    logger.info(f"Extracting text from: {pdf_path}")
    
    # This is a placeholder for the actual extraction logic
    # In a real implementation, this would handle complex PDF extraction
    reader = PdfReader(pdf_path)
    pages = []
    
    for i, page in tqdm(enumerate(reader.pages), total=len(reader.pages)):
        text = page.extract_text()
        pages.append({
            "page_number": i + 1,
            "text": text,
            "metadata": {
                "page_size": (page.mediabox.width, page.mediabox.height),
            }
        })
    
    logger.info(f"Extracted {len(pages)} pages from {pdf_path}")
    return pages


def extract_text_from_markdown(md_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from markdown file with metadata
    
    Returns:
        List of sections with text and metadata
    """
    logger.info(f"Extracting text from markdown: {md_path}")
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # For now, we'll treat the entire markdown as one section
        # In a more advanced implementation, you could split by headers
        return [{
            "section_number": 1,
            "text": content,
            "metadata": {
                "source_type": "markdown",
                "file_path": md_path
            }
        }]
    except Exception as e:
        logger.error(f"Error reading markdown file {md_path}: {str(e)}")
        raise


def extract_text_from_txt(txt_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from plain text file with metadata
    
    Returns:
        List of sections with text and metadata
    """
    logger.info(f"Extracting text from plain text file: {txt_path}")
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Return entire content as one section for verse-level processing
        return [{
            "section_number": 1,
            "text": content,
            "metadata": {
                "source_type": "text",
                "file_path": txt_path
            }
        }]
    except Exception as e:
        logger.error(f"Error reading text file {txt_path}: {str(e)}")
        raise


def process_text(pages: List[Dict[str, Any]], source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Clean and process extracted text based on source type
    
    Returns:
        Processed text sections with metadata
    """
    logger.info(f"Processing text for: {source_config['title']}")
    processed_sections = []

    # Handle plain text sources (like the Geneva Bible)
    try:
        if pages and isinstance(pages, list) and pages[0].get("metadata", {}).get("source_type") == "text":
            combined_text = "\n".join([p.get("text", "") for p in pages if p.get("text").strip()])
            
            # Clean up common text artifacts
            lines = combined_text.split('\n')
            cleaned_lines = []
            
            # Skip navigation lines and index rows
            skip_patterns = [
                "Verse index:", "Chapter index:", "↥", "↦", "⇈"
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip navigation and index lines
                if any(pattern in line for pattern in skip_patterns):
                    continue
                    
                # Skip lines that are just numbers (verse indices)
                if all(part.strip().isdigit() for part in line.split() if part.strip()):
                    continue
                    
                cleaned_lines.append(line)
            
            # Recombine cleaned text
            cleaned_text = "\n".join(cleaned_lines)
            
            processed_sections.append({
                "title": source_config.get("title", ""),
                "content": cleaned_text,
                "metadata": {
                    "source_id": source_config["id"],
                    "source_type": "scripture",
                    "language": source_config.get("language", "en"),
                    "version": source_config.get("version", ""),
                    "year": source_config.get("year", "")
                }
            })
            logger.info(f"Created {len(processed_sections)} processed sections (plain text)")
            return processed_sections
            
    except Exception as e:
        logger.warning(f"Error processing text: {e}", exc_info=True)
        # Fallback to generic processing
        pass

    # Generic processing for paginated sources (e.g., PDFs)
    current_section = {"title": "", "content": "", "metadata": {}}
    
    for page in tqdm(pages):
        # For demonstration purposes only
        text = page["text"]
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Very simplistic section detection
            if line.isupper() and len(line) < 100:
                # Save previous section if it exists
                if current_section["content"]:
                    processed_sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": line,
                    "content": "",
                    "metadata": {
                        "page_start": page.get("page_number"),
                        "source_id": source_config["id"]
                    }
                }
            else:
                current_section["content"] += line + "\n"
        
        # Update page end
        current_section["metadata"]["page_end"] = page.get("page_number")
    
    # Add final section
    if current_section["content"]:
        processed_sections.append(current_section)
    
    logger.info(f"Created {len(processed_sections)} processed sections")
    return processed_sections


def chunk_text(processed_sections: List[Dict[str, Any]], 
               source_config: Dict[str, Any], 
               chunking_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunk processed text according to strategy
    
    Returns:
        List of text chunks ready for vectorization
    """
    logger.info(f"Chunking text for: {source_config['title']}")
    
    # Get chunking strategy from source config
    strategy_name = source_config.get("chunking_strategy", "default")
    strategy = chunking_config["strategies"].get(strategy_name, chunking_config["default"])
    
    chunks = []
    chunk_id = 0
    
    # Handle verse-level chunking for Bible texts
    if strategy_name == "verse":
        return chunk_bible_text(processed_sections, source_config, strategy)
    
    # Default paragraph chunking for non-Bible texts
    for section in tqdm(processed_sections):
        content = section["content"]
        
        # Basic chunking by paragraphs
        paragraphs = content.split("\n\n")
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            # Create chunk with metadata
            chunk_id += 1
            chunk = {
                "id": f"{source_config['id']}_{chunk_id:06d}",
                "text": paragraph.strip(),
                "metadata": {
                    "source_id": source_config["id"],
                    "title": source_config["title"],
                    "author": source_config["author"],
                    "domain": "theology",
                    "section_title": section["title"],
                    "chunk_index": i,
                    "page_reference": f"{section['metadata'].get('page_start', 'unknown')}-{section['metadata'].get('page_end', 'unknown')}",
                    "chunk_strategy": strategy_name,
                    "creation_timestamp": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks


def chunk_bible_text(processed_sections: List[Dict[str, Any]], 
                    source_config: Dict[str, Any], 
                    strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Specialized chunking for Bible texts at verse level.
    This parser is optimized for clean TXT where each verse is either:
      - "Book Name Chapter:Verse Text..."
      - "Chapter:Verse Text..." (with current book inferred)
      - "Verse Text..." (with current book+chapter inferred)
    It also attempts to cope with common PDF-to-text artifacts (CHAPTER headings, small caps).
    """
    import re

    # Helpers
    def flush_chunk():
        nonlocal chunk_id, current_verses, current_verse_texts
        if current_verse_texts:
            chunk_id += 1
            chunks.append(
                create_verse_chunk(
                    chunk_id, source_config, current_book, current_chapter,
                    current_verses, current_verse_texts
                )
            )
            current_verses = []
            current_verse_texts = []

    def canonicalize_book(name: str) -> Optional[str]:
        n = name.strip()
        # Normalize multiple spaces
        n = re.sub(r"\s+", " ", n)
        # Common aliases and numerals
        aliases = {
            "Canticles": "Song of Solomon",
            "Song of Songs": "Song of Solomon",
            "Psalm": "Psalms",
            "I Samuel": "1 Samuel",
            "II Samuel": "2 Samuel",
            "I Kings": "1 Kings",
            "II Kings": "2 Kings",
            "I Chronicles": "1 Chronicles",
            "II Chronicles": "2 Chronicles",
            "I Corinthians": "1 Corinthians",
            "II Corinthians": "2 Corinthians",
            "I Thessalonians": "1 Thessalonians",
            "II Thessalonians": "2 Thessalonians",
            "I Timothy": "1 Timothy",
            "II Timothy": "2 Timothy",
            "I Peter": "1 Peter",
            "II Peter": "2 Peter",
            "I John": "1 John",
            "II John": "2 John",
            "III John": "3 John",
        }
        if n in aliases:
            n = aliases[n]
        # Accept only valid canonical names
        return n if n in canonical_books else None

    # Canonical list
    canonical_books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
        "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
        "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes",
        "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
        "Zephaniah", "Haggai", "Zechariah", "Malachi",
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
        "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
    ]

    # Regexes
    full_ref_re = re.compile(r"^\s*([1-3]?\s?[A-Za-z][A-Za-z ]+?)\s+(\d{1,3}):(\d{1,3}(?:-\d{1,3})?)\s+(.*\S)\s*$")
    book_chap_re = re.compile(r"^\s*([1-3]?\s?[A-Za-z][A-Za-z ]+?)\s+(\d{1,3})\s*$")
    chap_verse_re = re.compile(r"^\s*(\d{1,3}):(\d{1,3}(?:-\d{1,3})?)\s+(.*\S)\s*$")
    chapter_header_re = re.compile(r"^(?:Chapter|CHAPTER|CHAP\.?|CH\.?)\s+(\d{1,3})\s*$", re.IGNORECASE)
    verse_only_re = re.compile(r"^\s*(\d{1,3})\s+(.*\S)\s*$")  # requires book+chapter context
    index_row_re = re.compile(r"^\s*\d{1,3}(?:\s+\d{1,3})+\s*$")  # rows like "01 02 03 04..."
    
    # Patterns to skip (navigation, page numbers, etc.)
    skip_patterns = [
        r"^\s*\[?Page\s+\d+\]?\s*$",  # Page numbers
        r"^\s*\*\s*\*\s*\*\s*$",  # Separators like "* * *"
        r"^\s*\-+\s*$",  # Lines with just dashes
        r"^\s*\[.*\]\s*$",  # Anything in brackets (often footnotes)
        r"^\s*[ivxlcdm]+\s*$",  # Roman numerals (often in TOC)
        r"^\s*\d+\s*$",  # Standalone numbers
        r"^\s*(?:Verse|Chapter|Book|Index|Contents).*$",  # Section headers
    ]
    skip_regexes = [re.compile(p, re.IGNORECASE) for p in skip_patterns]

    chunks: List[Dict[str, Any]] = []
    chunk_id = 0
    max_verses = strategy.get("max_verses_per_chunk", 5)
    
    current_book: str = "Unknown"
    current_chapter: str = "1"
    current_verses: List[str] = []
    current_verse_texts: List[str] = []

    for section in tqdm(processed_sections):
        content = section.get("content") or section.get("text") or ""
        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            # Skip navigation/artifact lines common in ebook formats
            if line.startswith(("↥", "↦", "⇈")) or line.startswith("Chapter index:") or line.startswith("Verse index:"):
                continue
            # Skip rows that are just a list of verse numbers (index rows)
            if index_row_re.match(line):
                continue

            # 1) Full reference on one line: "Book 1:1 Text"
            m = full_ref_re.match(line)
            if m:
                flush_chunk()
                book_raw, chap, verse, vtext = m.groups()
                book = canonicalize_book(book_raw)
                if not book:
                    # Not a recognized book; skip line
                    continue
                current_book = book
                current_chapter = chap
                current_verses = [verse]
                current_verse_texts = [vtext]
                # Flush if chunk filled in one go (rare)
                if len(current_verses) >= max_verses:
                    flush_chunk()
                continue
            # 1b) Book and chapter header on one line: "Genesis 1"
            m = book_chap_re.match(line)
            if m:
                flush_chunk()
                book_raw, chap = m.groups()
                book = canonicalize_book(book_raw)
                if book:
                    current_book = book
                    current_chapter = chap
                continue

            # 2) Chapter heading only
            m = chapter_header_re.match(line)
            if m and current_book != "Unknown":
                flush_chunk()
                current_chapter = m.group(1)
                continue

            # 3) Chapter:Verse within current book
            m = chap_verse_re.match(line)
            if m and current_book != "Unknown":
                chap, verse, vtext = m.groups()
                if chap != current_chapter:
                    flush_chunk()
                    current_chapter = chap
                # If we have max verses, flush before appending
                if len(current_verses) >= max_verses:
                    flush_chunk()
                current_verses.append(verse)
                current_verse_texts.append(vtext)
                continue

            # 4) Verse only (requires current book+chapter)
            m = verse_only_re.match(line)
            if m and current_book != "Unknown" and current_chapter:
                verse, vtext = m.groups()
                # Guard against false positives: ignore very large verse numbers
                try:
                    vnum = int(verse.split("-")[0])
                except Exception:
                    vnum = 0
                if 0 < vnum <= 200:
                    if len(current_verses) >= max_verses:
                        flush_chunk()
                    current_verses.append(verse)
                    current_verse_texts.append(vtext)
                    continue

            # 5) Continuation of previous verse
            if current_verse_texts:
                current_verse_texts[-1] += " " + line

    # Flush remaining
    flush_chunk()

    logger.info(f"Created {len(chunks)} verse chunks")
    return chunks


def create_verse_chunk(chunk_id: int, source_config: Dict[str, Any], 
                      book: str, chapter: str, verses: List[str], 
                      verse_texts: List[str]) -> Dict[str, Any]:
    """Create a properly formatted verse chunk"""
    
    # Combine verse texts
    combined_text = " ".join(verse_texts)
    
    # Create verse reference
    if len(verses) == 1:
        verse_ref = f"{book} {chapter}:{verses[0]}"
    else:
        verse_ref = f"{book} {chapter}:{verses[0]}-{verses[-1]}"
    
    return {
        "id": f"{source_config['id']}_{chunk_id:06d}",
        "text": combined_text,
        "metadata": {
            "source_id": source_config["id"],
            "title": source_config["title"],
            "author": source_config["author"],
            "domain": "theology",
            "book_name": book,
            "chapter_number": chapter,
            "verse_numbers": ",".join(verses),
            "verse_reference": verse_ref,
            "testament": "Old" if book in [
                "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
                "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", 
                "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", 
                "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
                "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", 
                "Zephaniah", "Haggai", "Zechariah", "Malachi"
            ] else "New",
            "chunk_strategy": "verse",
            "creation_timestamp": datetime.now().isoformat()
        }
    }


def save_processed_data(sections: List[Dict[str, Any]], 
                       source_config: Dict[str, Any], 
                       domain: str):
    """Save processed text sections to disk"""
    source_id = source_config["id"]
    output_dir = BASE_DIR / "domains" / domain / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{source_id}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "source_id": source_id,
            "title": source_config["title"],
            "sections": sections
        }, f, indent=2)
    
    logger.info(f"Saved processed data to {output_file}")


def save_chunks(chunks: List[Dict[str, Any]], 
               source_config: Dict[str, Any], 
               domain: str):
    """Save text chunks to disk"""
    source_id = source_config["id"]
    output_dir = BASE_DIR / "domains" / domain / "chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{source_id}_chunks.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "source_id": source_id,
            "title": source_config["title"],
            "chunks": chunks
        }, f, indent=2)
    
    logger.info(f"Saved chunks to {output_file}")


def vectorize_chunks(chunks: List[Dict[str, Any]], 
                    models_config: Dict[str, Any],
                    domain: str):
    """Generate embeddings and store in ChromaDB"""
    # Skip if no chunks to process
    if not chunks:
        logger.warning("No chunks to vectorize, skipping...")
        return
        
    # Load embedding model
    domain_model = models_config["embeddings"].get("domain_specific", {}).get(domain, {})
    default_model = models_config["embeddings"]["default"]
    model_name = domain_model.get("name") or default_model["name"]
    local_path = domain_model.get("local_path") or default_model.get("local_path")
    
    logger.info(f"Loading embedding model: {local_path or model_name}")
    model = SentenceTransformer(local_path) if local_path else SentenceTransformer(model_name)
    
    # Initialize ChromaDB
    db_path = BASE_DIR / "vectordb"
    db_path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Get or create collection
    collection_name = models_config["vector_db"]["collections"].get(domain, {}).get("name", domain)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=None  # We'll handle embeddings ourselves
    )
    
    # Prepare data for insertion
    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Generate embeddings in batches
    batch_size = 32
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch_ids = ids[i:i+batch_size]
        batch_texts = texts[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        # Generate embeddings
        batch_embeddings = model.encode(batch_texts).tolist()
        
        # Add to ChromaDB
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas
        )
    
    logger.info(f"Added {len(chunks)} embeddings to ChromaDB collection '{collection_name}'")


def process_source(source_config: Dict[str, Any], 
                  chunking_config: Dict[str, Any],
                  models_config: Dict[str, Any],
                  domain: str):
    """Process a single source from raw file to vector database"""
    logger.info(f"Processing source: {source_config['title']}")
    
    # Resolve path
    source_path = BASE_DIR / source_config["path"]
    
    if not source_path.exists():
        logger.error(f"Source file not found: {source_path}")
        return
    
    # Extract text based on file type
    file_ext = source_path.suffix.lower()
    if file_ext == '.pdf':
        sections = extract_text_from_pdf(str(source_path))
    elif file_ext in ['.md', '.markdown']:
        sections = extract_text_from_markdown(str(source_path))
    elif file_ext in ['.txt', '.text']:
        sections = extract_text_from_txt(str(source_path))
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        return
    
    # Process text
    processed_sections = process_text(sections, source_config)
    
    # Save processed data
    save_processed_data(processed_sections, source_config, domain)
    
    # Chunk text
    chunks = chunk_text(processed_sections, source_config, chunking_config)
    
    # Save chunks
    save_chunks(chunks, source_config, domain)

    # If no chunks were produced, skip vectorization to avoid unnecessary failures
    if not chunks:
        logger.warning("No chunks created; skipping vectorization.")
        return
    
    # Vectorize and store in ChromaDB
    vectorize_chunks(chunks, models_config, domain)
    
    logger.info(f"Completed processing: {source_config['title']}")


def main():
    parser = argparse.ArgumentParser(description="TinyOwl Ingestion Script")
    parser.add_argument("--config", default="configs/sources.yaml", help="Path to sources configuration")
    parser.add_argument("--domain", default="theology", help="Domain to process")
    parser.add_argument("--source-id", help="Optional: Process only this source ID")
    args = parser.parse_args()
    
    # Load configurations
    sources_config = load_config(args.config)
    chunking_config = load_config(BASE_DIR / "configs" / "chunking.yaml")
    models_config = load_config(BASE_DIR / "configs" / "models.yaml")
    
    domain = args.domain or sources_config.get("domain", "theology")
    logger.info(f"Processing domain: {domain}")
    
    # Process sources
    for source in sources_config["sources"]:
        if args.source_id and source["id"] != args.source_id:
            continue
            
        process_source(source, chunking_config, models_config, domain)
    
    logger.info("Ingestion process completed!")


if __name__ == "__main__":
    main()
