#!/usr/bin/env python3
"""
TinyOwl Precise KJV Ingestion
Handles the exact KJV format structure with bulletproof parsing
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Import our bulletproof components
from text_normalizer import TextNormalizer
from canonical_validator import CanonicalValidator

class PreciseKJVIngestor:
    """Precise KJV ingestion with exact format handling"""
    
    def __init__(self, output_dir: str = "domains/theology"):
        self.output_dir = Path(output_dir)
        self.normalizer = TextNormalizer()
        self.validator = CanonicalValidator()
        
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "chunks").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
    
    def ingest_kjv_bible(self, filepath: str, translation_id: str = "kjv") -> Dict[str, Any]:
        """Complete bulletproof ingestion of KJV Bible text"""
        print("🎯 Starting Precise KJV Ingestion Pipeline")
        print("=" * 60)
        
        start_time = time.time()
        report = {
            "translation_id": translation_id,
            "source_file": filepath,
            "start_time": start_time,
            "stages": {}
        }
        
        try:
            # Stage 1: Parse with exact format understanding
            verses_data = self._parse_kjv_format(filepath, translation_id, report)
            
            # Stage 2: Validate coverage
            validated_data = self._validate_coverage(verses_data, translation_id, report)
            
            # Stage 3: Create hierarchical chunks
            hierarchical_chunks = self._create_hierarchical_chunks(validated_data, translation_id, report)
            
            # Stage 4: Save chunks
            self._save_chunks(hierarchical_chunks, translation_id, report)
            
            # Stage 5: Quality assessment
            self._quality_assessment(hierarchical_chunks, translation_id, report)
            
        except Exception as e:
            print(f"❌ PIPELINE FAILED: {e}")
            report["success"] = False
            report["error"] = str(e)
            return report
        
        # Success!
        report["success"] = True
        report["total_time"] = time.time() - start_time
        
        print(f"\n🎉 PRECISE KJV INGESTION COMPLETE!")
        print(f"⏱️  Total time: {report['total_time']:.2f} seconds")
        
        return report
    
    def _parse_kjv_format(self, filepath: str, translation_id: str, report: Dict) -> Dict[str, Dict[int, Dict[int, str]]]:
        """Parse KJV with exact format understanding"""
        print("\n📖 Stage 1: Precise KJV Format Parsing")
        stage_start = time.time()
        
        # Load file
        with open(filepath, 'r', encoding='latin1') as f:
            lines = f.readlines()
        
        print(f"   📄 Loaded {len(lines):,} lines")
        
        # Define the 66 canonical books in order with their KJV titles
        kjv_books = [
            ("THE FIRST BOOK OF MOSES, CALLED", "GENESIS", "Gen"),
            ("THE SECOND BOOK OF MOSES, CALLED", "EXODUS", "Exod"), 
            ("THE THIRD BOOK OF MOSES, CALLED", "LEVITICUS", "Lev"),
            ("THE FOURTH BOOK OF MOSES, CALLED", "NUMBERS", "Num"),
            ("THE FIFTH BOOK OF MOSES, CALLED", "DEUTERONOMY", "Deut"),
            ("THE BOOK OF", "JOSHUA", "Josh"),
            ("THE BOOK OF", "JUDGES", "Judg"),
            ("THE BOOK OF", "RUTH", "Ruth"),
            ("", "FIRST BOOK OF SAMUEL", "1Sam"),
            ("", "SECOND BOOK OF SAMUEL", "2Sam"),
            ("", "FIRST BOOK OF THE KINGS", "1Kgs"),
            ("", "SECOND BOOK OF THE KINGS", "2Kgs"),
            ("THE FIRST BOOK OF THE", "CHRONICLES", "1Chr"),
            ("THE SECOND BOOK OF THE", "CHRONICLES", "2Chr"),
            ("", "EZRA", "Ezra"),
            ("THE BOOK OF", "NEHEMIAH", "Neh"),
            ("THE BOOK OF", "ESTHER", "Esth"),
            ("THE BOOK OF", "JOB", "Job"),
            ("THE BOOK OF", "PSALMS", "Ps"),
            ("", "THE PROVERBS", "Prov"),
            ("", "ECCLESIASTES", "Eccl"),
            ("", "THE SONG OF SOLOMON", "Song"),
            ("THE BOOK OF THE PROPHET", "ISAIAH", "Isa"),
            ("THE BOOK OF THE PROPHET", "JEREMIAH", "Jer"),
            ("", "THE LAMENTATIONS OF JEREMIAH", "Lam"),
            ("THE BOOK OF THE PROPHET", "EZEKIEL", "Ezek"),
            ("THE BOOK OF", "DANIEL", "Dan"),
            ("", "HOSEA", "Hos"),
            ("", "JOEL", "Joel"),
            ("", "AMOS", "Amos"),
            ("", "OBADIAH", "Obad"),
            ("", "JONAH", "Jonah"),
            ("", "MICAH", "Mic"),
            ("", "NAHUM", "Nah"),
            ("", "HABAKKUK", "Hab"),
            ("", "ZEPHANIAH", "Zeph"),
            ("", "HAGGAI", "Hag"),
            ("", "ZECHARIAH", "Zech"),
            ("", "MALACHI", "Mal"),
            ("THE GOSPEL ACCORDING TO", "SAINT MATTHEW", "Matt"),
            ("THE GOSPEL ACCORDING TO", "SAINT MARK", "Mark"),
            ("THE GOSPEL ACCORDING TO", "SAINT LUKE", "Luke"),
            ("THE GOSPEL ACCORDING TO", "SAINT JOHN", "John"),
            ("", "THE ACTS OF THE APOSTLES", "Acts"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "ROMANS", "Rom"),
            ("THE FIRST EPISTLE OF PAUL THE APOSTLE TO THE", "CORINTHIANS", "1Cor"),
            ("THE SECOND EPISTLE OF PAUL THE APOSTLE TO THE", "CORINTHIANS", "2Cor"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "GALATIANS", "Gal"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "EPHESIANS", "Eph"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "PHILIPPIANS", "Phil"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "COLOSSIANS", "Col"),
            ("THE FIRST EPISTLE OF PAUL THE APOSTLE TO THE", "THESSALONIANS", "1Thess"),
            ("THE SECOND EPISTLE OF PAUL THE APOSTLE TO THE", "THESSALONIANS", "2Thess"),
            ("THE FIRST EPISTLE OF PAUL THE APOSTLE TO", "TIMOTHY", "1Tim"),
            ("THE SECOND EPISTLE OF PAUL THE APOSTLE TO", "TIMOTHY", "2Tim"),
            ("THE EPISTLE OF PAUL TO", "TITUS", "Titus"),
            ("THE EPISTLE OF PAUL TO", "PHILEMON", "Phlm"),
            ("THE EPISTLE OF PAUL THE APOSTLE TO THE", "HEBREWS", "Heb"),
            ("THE GENERAL EPISTLE OF", "JAMES", "Jas"),
            ("THE FIRST EPISTLE GENERAL OF", "PETER", "1Pet"),
            ("THE SECOND EPISTLE GENERAL OF", "PETER", "2Pet"),
            ("THE FIRST GENERAL EPISTLE OF", "JOHN", "1John"),
            ("THE SECOND EPISTLE OF", "JOHN", "2John"),
            ("THE THIRD EPISTLE OF", "JOHN", "3John"),
            ("THE GENERAL EPISTLE OF", "JUDE", "Jude"),
            ("", "THE REVELATION", "Rev")
        ]
        
        # Create mapping for quick lookup
        book_lookup = {}
        for prefix, suffix, book_id in kjv_books:
            if prefix:
                key = f"{prefix}|{suffix}"
            else:
                key = suffix
            book_lookup[key] = book_id
        
        # Parse the text
        verses_data = defaultdict(lambda: defaultdict(dict))
        current_book_id = None
        current_chapter = None
        verse_count = 0
        books_found = []
        
        # Patterns
        chapter_pattern = re.compile(r'^CHAPTER\s+(\d+)$', re.IGNORECASE)
        verse_pattern = re.compile(r'^\s*(\d+)\s+(.+)$')
        
        # Track processed books to avoid duplicates
        processed_books = set()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for book markers (but avoid duplicates)
            book_found = False
            for prefix, suffix, book_id in kjv_books:
                # Skip if we've already processed this book
                if book_id in processed_books:
                    continue
                    
                if prefix:
                    # Two-line pattern: prefix then suffix
                    if (line == prefix and 
                        i + 1 < len(lines) and 
                        lines[i + 1].strip() == suffix):
                        current_book_id = book_id
                        books_found.append(book_id)
                        processed_books.add(book_id)
                        current_chapter = None
                        print(f"   📖 Found: {book_id} ({prefix} {suffix})")
                        book_found = True
                        i += 2  # Skip both lines
                        break
                else:
                    # Single line pattern
                    if line == suffix:
                        current_book_id = book_id
                        books_found.append(book_id)
                        processed_books.add(book_id)
                        current_chapter = None
                        print(f"   📖 Found: {book_id} ({suffix})")
                        book_found = True
                        i += 1
                        break
            
            if book_found:
                continue
            
            # Skip if we haven't found a book yet
            if not current_book_id:
                i += 1
                continue
            
            # Check for chapter markers
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                current_chapter = int(chapter_match.group(1))
                i += 1
                continue
            
            # Check for verses
            verse_match = verse_pattern.match(line)
            if verse_match and current_chapter:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                # Normalize text
                normalized_text = self.normalizer.normalize_text(verse_text)
                
                # Store verse
                verses_data[current_book_id][current_chapter][verse_num] = normalized_text
                verse_count += 1
                
                if verse_count % 5000 == 0:
                    print(f"   ⚡ Processed {verse_count:,} verses...")
            
            i += 1
        
        print(f"   ✅ Processed {verse_count:,} verses from {len(books_found)} books")
        print(f"   📚 Books found: {', '.join(books_found)}")
        
        report["stages"]["stage_1"] = {
            "name": "Precise KJV Parsing",
            "verses_processed": verse_count,
            "books_found": len(books_found),
            "books_list": books_found,
            "time_seconds": time.time() - stage_start
        }
        
        return verses_data
    
    def _validate_coverage(self, verses_data: Dict, translation_id: str, report: Dict) -> Dict:
        """Validate canonical coverage"""
        print("\n🔍 Stage 2: Canonical Coverage Validation")
        stage_start = time.time()
        
        validation_report = self.validator.run_comprehensive_validation(verses_data)
        
        print(f"   📊 Coverage: {validation_report['summary']['coverage_percentage']:.2f}%")
        print(f"   ✅ Valid: {validation_report['summary']['is_valid']}")
        print(f"   ⚠️  Errors: {validation_report['summary']['error_count']}")
        
        for rec in validation_report['recommendations']:
            if '✅' in rec:
                print(f"   {rec}")
            elif 'CRITICAL' in rec or '❌' in rec:
                print(f"   🚨 {rec}")
        
        if not validation_report['summary']['is_valid']:
            print(f"\n🔍 Validation Details:")
            if validation_report['missing_content']['books']:
                print(f"   Missing books: {validation_report['missing_content']['books']}")
            if len(validation_report['missing_content']['verses']) < 50:  # Show if not too many
                missing_verses = validation_report['missing_content']['verses'][:10]
                print(f"   Sample missing verses: {[v['osis_id'] for v in missing_verses]}")
        
        report["stages"]["stage_2"] = {
            "name": "Canonical Validation",
            "coverage_percentage": validation_report['summary']['coverage_percentage'],
            "is_valid": validation_report['summary']['is_valid'],
            "error_count": validation_report['summary']['error_count'],
            "validation_report": validation_report,
            "time_seconds": time.time() - stage_start
        }
        
        if not validation_report['summary']['is_valid'] and validation_report['summary']['coverage_percentage'] < 95:
            raise ValueError("Coverage too low - manual inspection required")
        
        return verses_data
    
    def _create_hierarchical_chunks(self, verses_data: Dict, translation_id: str, report: Dict) -> Dict:
        """Create hierarchical chunks"""
        print("\n🏗️  Stage 3: Hierarchical Chunking")
        stage_start = time.time()
        
        hierarchical_chunks = {
            "verses": [],
            "pericopes": [], 
            "chapters": []
        }
        
        for book_id, chapters in verses_data.items():
            for chapter_num, verses in chapters.items():
                # Verse chunks (Layer A)
                for verse_num, verse_text in verses.items():
                    osis_id = self.normalizer.create_osis_id(book_id, chapter_num, verse_num)
                    
                    verse_chunk = {
                        "id": f"{translation_id}_{osis_id.lower().replace('.', '_')}",
                        "osis_id": osis_id,
                        "content": verse_text,
                        "metadata": {
                            "source_id": translation_id,
                            "type": "scripture",
                            "layer": "verse",
                            "book_id": book_id,
                            "chapter": chapter_num,
                            "verse": verse_num,
                            "authority_level": "scripture",
                            "translation": "KJV"
                        }
                    }
                    hierarchical_chunks["verses"].append(verse_chunk)
                
                # Pericope chunks (Layer B)
                verse_list = sorted(verses.items())
                window_size = 6
                stride = 3
                
                for i in range(0, len(verse_list), stride):
                    window_verses = verse_list[i:i + window_size]
                    if len(window_verses) < 3:
                        continue
                    
                    start_verse = window_verses[0][0]
                    end_verse = window_verses[-1][0]
                    combined_text = " ".join([verse_text for _, verse_text in window_verses])
                    
                    pericope_chunk = {
                        "id": f"{translation_id}_{book_id.lower()}_c{chapter_num:02d}_p{i+1:03d}",
                        "osis_id_start": self.normalizer.create_osis_id(book_id, chapter_num, start_verse),
                        "osis_id_end": self.normalizer.create_osis_id(book_id, chapter_num, end_verse),
                        "content": combined_text,
                        "metadata": {
                            "source_id": translation_id,
                            "type": "scripture",
                            "layer": "pericope", 
                            "book_id": book_id,
                            "chapter": chapter_num,
                            "verse_start": start_verse,
                            "verse_end": end_verse,
                            "authority_level": "scripture",
                            "translation": "KJV"
                        }
                    }
                    hierarchical_chunks["pericopes"].append(pericope_chunk)
                
                # Chapter chunk (Layer C)
                all_verses_text = " ".join([verse_text for _, verse_text in verse_list])
                chapter_chunk = {
                    "id": f"{translation_id}_{book_id.lower()}_chapter_{chapter_num:02d}",
                    "osis_id_start": self.normalizer.create_osis_id(book_id, chapter_num, 1),
                    "content": all_verses_text,
                    "metadata": {
                        "source_id": translation_id,
                        "type": "scripture",
                        "layer": "chapter",
                        "book_id": book_id,
                        "chapter": chapter_num,
                        "verse_count": len(verses),
                        "authority_level": "scripture",
                        "translation": "KJV"
                    }
                }
                hierarchical_chunks["chapters"].append(chapter_chunk)
        
        verse_count = len(hierarchical_chunks["verses"])
        pericope_count = len(hierarchical_chunks["pericopes"]) 
        chapter_count = len(hierarchical_chunks["chapters"])
        total_chunks = verse_count + pericope_count + chapter_count
        
        print(f"   ✅ Created {total_chunks:,} hierarchical chunks:")
        print(f"      📝 {verse_count:,} verse chunks")
        print(f"      📖 {pericope_count:,} pericope chunks")
        print(f"      📚 {chapter_count:,} chapter chunks")
        
        report["stages"]["stage_3"] = {
            "name": "Hierarchical Chunking",
            "verse_chunks": verse_count,
            "pericope_chunks": pericope_count, 
            "chapter_chunks": chapter_count,
            "total_chunks": total_chunks,
            "time_seconds": time.time() - stage_start
        }
        
        return hierarchical_chunks
    
    def _save_chunks(self, hierarchical_chunks: Dict, translation_id: str, report: Dict) -> None:
        """Save chunk layers"""
        print("\n💾 Stage 4: Saving Hierarchical Chunks")
        stage_start = time.time()
        
        for layer_name, chunks in hierarchical_chunks.items():
            filename = f"{translation_id}_{layer_name}_chunks.json"
            filepath = self.output_dir / "chunks" / filename
            
            chunk_data = {
                "translation_id": translation_id,
                "layer": layer_name,
                "chunk_count": len(chunks),
                "chunks": chunks,
                "created_timestamp": time.time()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Saved {len(chunks):,} {layer_name} chunks → {filename}")
        
        report["stages"]["stage_4"] = {
            "name": "Save Chunks",
            "files_created": len(hierarchical_chunks),
            "time_seconds": time.time() - stage_start
        }
    
    def _quality_assessment(self, hierarchical_chunks: Dict, translation_id: str, report: Dict) -> None:
        """Final quality assessment"""
        print("\n🏆 Stage 5: Quality Assessment")
        stage_start = time.time()
        
        total_chunks = sum(len(chunks) for chunks in hierarchical_chunks.values())
        verse_chunks = len(hierarchical_chunks["verses"])
        expected_verses = 31102
        coverage_quality = (verse_chunks / expected_verses) * 100
        
        print(f"   📊 Quality Metrics:")
        print(f"      Coverage: {coverage_quality:.2f}% ({verse_chunks}/{expected_verses})")
        print(f"      Total chunks: {total_chunks:,}")
        
        quality_score = 0
        if coverage_quality >= 99:
            quality_score += 2
            print(f"      ✅ Excellent coverage: +2")
        elif coverage_quality >= 95:
            quality_score += 1
            print(f"      ✅ Good coverage: +1")
        
        if total_chunks >= 40000:
            quality_score += 1
            print(f"      ✅ Rich hierarchical data: +1")
        
        print(f"   🏆 Final Quality Score: {quality_score}/3")
        
        report["stages"]["stage_5"] = {
            "name": "Quality Assessment",
            "quality_score": quality_score,
            "coverage_quality": coverage_quality,
            "total_chunks": total_chunks,
            "time_seconds": time.time() - stage_start
        }


if __name__ == "__main__":
    ingestor = PreciseKJVIngestor()
    
    kjv_path = "/home/nigel/Downloads/TheHolyBibleKJV.txt"
    report = ingestor.ingest_kjv_bible(kjv_path, "kjv")
    
    # Save report
    with open("domains/theology/processed/kjv_precise_ingestion_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Report saved to: domains/theology/processed/kjv_precise_ingestion_report.json")