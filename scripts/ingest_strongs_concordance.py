#!/usr/bin/env python3
"""
Strong's Exhaustive Concordance Bridge Integration for TinyOwl
============================================================

Bridges Strong's Concordance to TinyOwl's existing OSIS canonical system:
- Uses existing TextNormalizer for book name conversion
- Links Strong's entries to existing KJV/WEB verse chunks via OSIS IDs
- Creates concordance lookup layers without disrupting existing embeddings
- Adds Hebrew/Greek Strong's numbers as enrichment data

Architecture:
    Strong's Format: "Exo. 4:14 [H175]"
           ↓ (TextNormalizer)
    OSIS Format: "Exod.04.014" 
           ↓ (lookup existing chunks)
    Result: Link to embedded verse + Strong's metadata

Usage:
    python scripts/ingest_strongs_concordance.py
"""

import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import sys
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from scripts.text_normalizer import TextNormalizer


@dataclass
class ConcordanceEntry:
    """Individual concordance entry linking word to verse with Strong's number."""
    word: str
    osis_id: str
    book: str
    chapter: int
    verse: int
    context: str
    strong_number: Optional[str] = None
    testament: str = "OT"
    source: str = "strongs_concordance"


@dataclass
class StrongsNumber:
    """Strong's dictionary entry with associated words."""
    number: str
    type: str  # "H" for Hebrew, "G" for Greek
    word_entries: List[str]
    verse_count: int
    testament: str
    source: str = "strongs_concordance"


class StrongsConcordanceBridge:
    """Bridge Strong's Concordance to TinyOwl's OSIS system."""
    
    def __init__(self, markdown_file: Path):
        self.markdown_file = markdown_file
        self.text_normalizer = TextNormalizer()
        self.entries: List[ConcordanceEntry] = []
        self.strongs_numbers: Dict[str, StrongsNumber] = {}
        self.failed_mappings: Set[str] = set()
        self.success_count = 0
        self.total_count = 0
        
    def parse_and_bridge(self) -> Tuple[List[ConcordanceEntry], List[StrongsNumber]]:
        """Parse concordance and bridge to OSIS system."""
        logging.info(f"Parsing Strong's Concordance from {self.markdown_file}")
        
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find start of concordance entries (skip introduction)
        concordance_start = content.find("AARON")
        if concordance_start == -1:
            raise ValueError("Could not find start of concordance entries")
        
        concordance_content = content[concordance_start:]
        
        # Parse entries
        current_word = None
        
        for line in concordance_content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts new word entry (all caps word)
            word_match = re.match(r'^([A-Z\'-]+)\s+(.+)', line)
            if word_match:
                current_word = word_match.group(1)
                rest_of_line = word_match.group(2)
                self._process_word_line(current_word, rest_of_line)
                
            elif current_word and line:
                # Continuation line for current word
                self._process_word_line(current_word, line)
        
        # Generate Strong's number summaries
        strongs_list = list(self.strongs_numbers.values())
        
        logging.info(f"✅ Processed {self.success_count}/{self.total_count} entries successfully")
        logging.info(f"   📖 {len(self.entries)} concordance entries created")
        logging.info(f"   🔢 {len(strongs_list)} unique Strong's numbers found")
        
        if self.failed_mappings:
            logging.warning(f"⚠️ {len(self.failed_mappings)} failed book mappings: {sorted(list(self.failed_mappings))[:10]}...")
        
        return self.entries, strongs_list
    
    def _process_word_line(self, word: str, line: str):
        """Process a line containing Bible references for a word."""
        # Pattern: BookRef Chapter:Verse context [HNumber or GNumber]
        pattern = r'([A-Za-z0-9\.]+)\s+(\d+):(\d+)\s+([^[]+?)(?:\s*\[([HG]\d+)\])?(?=\s+[A-Za-z0-9\.]+\s+\d+:|\s*$)'
        
        matches = re.finditer(pattern, line)
        
        for match in matches:
            self.total_count += 1
            
            book_abbrev = match.group(1).rstrip('.')
            chapter = int(match.group(2))
            verse = int(match.group(3))
            context = match.group(4).strip()
            strong_number = match.group(5) if match.group(5) else None
            
            # Bridge to OSIS system using TextNormalizer
            osis_id = self._bridge_to_osis(book_abbrev, chapter, verse)
            if not osis_id:
                self.failed_mappings.add(book_abbrev)
                continue
            
            # Extract canonical book name from OSIS ID
            canonical_book = osis_id.split('.')[0]
            
            # Determine testament based on canonical book
            testament = self._determine_testament(canonical_book)
            
            # Create concordance entry
            entry = ConcordanceEntry(
                word=word,
                osis_id=osis_id,
                book=canonical_book,
                chapter=chapter,
                verse=verse,
                context=context,
                strong_number=strong_number,
                testament=testament
            )
            self.entries.append(entry)
            self.success_count += 1
            
            # Track Strong's numbers
            if strong_number:
                if strong_number not in self.strongs_numbers:
                    self.strongs_numbers[strong_number] = StrongsNumber(
                        number=strong_number,
                        type=strong_number[0],  # "H" or "G"
                        word_entries=[word],
                        verse_count=1,
                        testament="NT" if strong_number.startswith("G") else "OT"
                    )
                else:
                    strongs_entry = self.strongs_numbers[strong_number]
                    if word not in strongs_entry.word_entries:
                        strongs_entry.word_entries.append(word)
                    strongs_entry.verse_count += 1
    
    def _bridge_to_osis(self, book_abbrev: str, chapter: int, verse: int) -> Optional[str]:
        """Bridge Strong's book abbreviation to OSIS ID using TextNormalizer."""
        # First try direct Strong's to OSIS mapping for common cases
        strongs_to_osis = {
            # Old Testament
            'Gen': 'Gen', 'Exo': 'Exod', 'Lev': 'Lev', 'Num': 'Num', 'Deu': 'Deut',
            'Jos': 'Josh', 'Jud': 'Judg', 'Rut': 'Ruth', 
            '1Sa': '1Sam', '2Sa': '2Sam', '1Ki': '1Kgs', '2Ki': '2Kgs',
            '1Ch': '1Chr', '2Ch': '2Chr', 'Ezr': 'Ezra', 'Neh': 'Neh', 'Est': 'Esth',
            'Job': 'Job', 'Psa': 'Ps', 'Pro': 'Prov', 'Ecc': 'Eccl', 'Sol': 'Song', 'Son': 'Song',
            'Isa': 'Isa', 'Jer': 'Jer', 'Lam': 'Lam', 'Eze': 'Ezek', 'Dan': 'Dan',
            'Hos': 'Hos', 'Joe': 'Joel', 'Amo': 'Amos', 'Oba': 'Obad', 'Jon': 'Jonah',
            'Mic': 'Mic', 'Nah': 'Nah', 'Hab': 'Hab', 'Zep': 'Zeph', 'Hag': 'Hag',
            'Zec': 'Zech', 'Mal': 'Mal',
            # New Testament  
            'Mat': 'Matt', 'Mar': 'Mark', 'Luk': 'Luke', 'Joh': 'John', 'Act': 'Acts',
            'Rom': 'Rom', '1Co': '1Cor', '2Co': '2Cor', 'Gal': 'Gal', 'Eph': 'Eph',
            'Php': 'Phil', 'Col': 'Col', '1Th': '1Thess', '2Th': '2Thess',
            '1Ti': '1Tim', '2Ti': '2Tim', 'Tit': 'Titus', 'Phm': 'Phlm', 'Heb': 'Heb',
            'Jas': 'Jas', 'Jam': 'Jas', '1Pe': '1Pet', '2Pe': '2Pet', 
            '1Jo': '1John', '2Jo': '2John', '3Jo': '3John', 'Jud': 'Jude', 'Rev': 'Rev'
        }
        
        # Try direct mapping first
        if book_abbrev in strongs_to_osis:
            canonical_book = strongs_to_osis[book_abbrev]
            osis_id = self.text_normalizer.create_osis_id(canonical_book, chapter, verse)
            return osis_id
        
        # Fallback to TextNormalizer for edge cases
        ref_text = f"{book_abbrev} {chapter}:{verse}"
        parsed_ref = self.text_normalizer.parse_verse_reference(ref_text)
        
        if parsed_ref and 'book_id' in parsed_ref:
            canonical_book = parsed_ref['book_id']
            osis_id = self.text_normalizer.create_osis_id(canonical_book, chapter, verse)
            return osis_id
        
        return None
    
    def _determine_testament(self, canonical_book: str) -> str:
        """Determine testament based on canonical book ID."""
        # NT books (standard OSIS IDs)
        nt_books = {
            "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", 
            "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", 
            "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", 
            "3John", "Jude", "Rev"
        }
        return "NT" if canonical_book in nt_books else "OT"


def create_concordance_chunks(entries: List[ConcordanceEntry], 
                            strongs_numbers: List[StrongsNumber]) -> Dict[str, List[Dict]]:
    """Create hierarchical chunks for concordance data."""
    
    # Layer 1: Word-verse concordance entries
    word_chunks = []
    for entry in entries:
        chunk = {
            "id": f"concordance_{entry.word.lower()}_{entry.osis_id}",
            "source": "strongs_concordance",
            "layer": "word_entry",
            "word": entry.word,
            "osis_id": entry.osis_id,
            "book": entry.book,
            "chapter": entry.chapter,
            "verse": entry.verse,
            "testament": entry.testament,
            "context": entry.context,
            "strong_number": entry.strong_number,
            "content": f"{entry.word} ({entry.osis_id}): {entry.context}" + 
                      (f" [Strong's {entry.strong_number}]" if entry.strong_number else ""),
            "metadata": {
                "entry_type": "concordance_word_entry",
                "word": entry.word,
                "strong_number": entry.strong_number,
                "testament": entry.testament,
                "osis_reference": entry.osis_id
            }
        }
        word_chunks.append(chunk)
    
    # Layer 2: Strong's number summaries
    strongs_chunks = []
    for strongs in strongs_numbers:
        chunk = {
            "id": f"strongs_{strongs.number.lower()}",
            "source": "strongs_concordance", 
            "layer": "strongs_number",
            "strong_number": strongs.number,
            "type": strongs.type,
            "testament": strongs.testament,
            "word_entries": strongs.word_entries,
            "verse_count": strongs.verse_count,
            "content": f"Strong's {strongs.number} ({strongs.type}): " + 
                      f"{len(strongs.word_entries)} words, {strongs.verse_count} verses. " +
                      f"Words: {', '.join(strongs.word_entries[:8])}" + 
                      ("..." if len(strongs.word_entries) > 8 else ""),
            "metadata": {
                "entry_type": "strongs_number",
                "strong_number": strongs.number,
                "type": strongs.type,
                "testament": strongs.testament,
                "word_count": len(strongs.word_entries),
                "verse_count": strongs.verse_count
            }
        }
        strongs_chunks.append(chunk)
    
    # Layer 3: Word summaries (grouped by word across all verses)
    word_summaries = {}
    for entry in entries:
        word = entry.word.lower()
        if word not in word_summaries:
            word_summaries[word] = {
                "word": entry.word,
                "verses": [],
                "strong_numbers": set(),
                "testament_counts": {"OT": 0, "NT": 0}
            }
        
        word_summaries[word]["verses"].append(entry.osis_id)
        word_summaries[word]["testament_counts"][entry.testament] += 1
        if entry.strong_number:
            word_summaries[word]["strong_numbers"].add(entry.strong_number)
    
    word_summary_chunks = []
    for word, data in word_summaries.items():
        total_verses = len(data["verses"])
        strong_numbers_list = sorted(list(data["strong_numbers"]))
        
        chunk = {
            "id": f"word_summary_{word}",
            "source": "strongs_concordance",
            "layer": "word_summary", 
            "word": data["word"],
            "total_verses": total_verses,
            "ot_count": data["testament_counts"]["OT"],
            "nt_count": data["testament_counts"]["NT"],
            "strong_numbers": strong_numbers_list,
            "content": f"{data['word']}: {total_verses} verses " +
                      f"(OT: {data['testament_counts']['OT']}, NT: {data['testament_counts']['NT']})" +
                      (f". Strong's: {', '.join(strong_numbers_list[:5])}" if strong_numbers_list else ""),
            "metadata": {
                "entry_type": "word_summary",
                "word": data["word"],
                "total_verses": total_verses,
                "testament_counts": data["testament_counts"],
                "strong_numbers": strong_numbers_list
            }
        }
        word_summary_chunks.append(chunk)
    
    return {
        "concordance_entries": word_chunks,
        "strongs_numbers": strongs_chunks, 
        "word_summaries": word_summary_chunks
    }


def save_chunks(chunks: Dict[str, List[Dict]], output_dir: Path):
    """Save chunks to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_chunks = 0
    for layer_name, layer_chunks in chunks.items():
        output_file = output_dir / f"strongs_{layer_name}_chunks.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(layer_chunks, f, indent=2, ensure_ascii=False)
        
        total_chunks += len(layer_chunks)
        logging.info(f"💾 Saved {len(layer_chunks)} {layer_name} chunks to {output_file}")
    
    logging.info(f"📊 Total chunks created: {total_chunks}")


def main():
    """Main concordance bridging workflow."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("🦉 TinyOwl Strong's Concordance Bridge Integration")
    
    # File paths
    markdown_file = PROJECT_ROOT / "domains" / "theology" / "raw" / "strongs_concordance.md"
    output_dir = PROJECT_ROOT / "domains" / "theology" / "chunks"
    
    if not markdown_file.exists():
        raise FileNotFoundError(f"Strong's concordance file not found: {markdown_file}")
    
    # Bridge the concordance
    bridge = StrongsConcordanceBridge(markdown_file)
    entries, strongs_numbers = bridge.parse_and_bridge()
    
    # Create hierarchical chunks
    chunks = create_concordance_chunks(entries, strongs_numbers)
    
    # Save chunks
    save_chunks(chunks, output_dir)
    
    logging.info("✅ Strong's Concordance bridge integration complete!")
    logging.info(f"   🔗 {len(chunks['concordance_entries'])} word-verse links")
    logging.info(f"   🔢 {len(chunks['strongs_numbers'])} Strong's numbers") 
    logging.info(f"   📝 {len(chunks['word_summaries'])} word summaries")
    logging.info("   🎯 Ready for @strong: and @word: hotkey lookups!")


if __name__ == "__main__":
    main()