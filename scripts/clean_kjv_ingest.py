#!/usr/bin/env python3
"""
TinyOwl Clean KJV Ingestion
Handles the perfect clean format: "Genesis 1:1\tVerse text"
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

class CleanKJVIngestor:
    """Clean KJV ingestion with simple tab-delimited format"""
    
    def __init__(self, output_dir: str = "domains/theology"):
        self.output_dir = Path(output_dir)
        self.normalizer = TextNormalizer()
        self.validator = CanonicalValidator()
        
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "chunks").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
    
    def ingest_kjv_bible(self, filepath: str, translation_id: str = "kjv") -> Dict[str, Any]:
        """Complete bulletproof ingestion of clean KJV format"""
        print("🎯 Starting Clean KJV Ingestion Pipeline")
        print("=" * 60)
        
        start_time = time.time()
        report = {
            "translation_id": translation_id,
            "source_file": filepath,
            "start_time": start_time,
            "stages": {}
        }
        
        try:
            # Stage 1: Parse clean format
            verses_data = self._parse_clean_format(filepath, translation_id, report)
            
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
        
        print(f"\n🎉 CLEAN KJV INGESTION COMPLETE!")
        print(f"⏱️  Total time: {report['total_time']:.2f} seconds")
        
        return report
    
    def _parse_clean_format(self, filepath: str, translation_id: str, report: Dict) -> Dict[str, Dict[int, Dict[int, str]]]:
        """Parse the clean tab-delimited format"""
        print("\n📖 Stage 1: Clean Format Parsing")
        stage_start = time.time()
        
        # Load file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"   📄 Loaded {len(lines):,} lines")
        
        # Parse verses
        verses_data = defaultdict(lambda: defaultdict(dict))
        verse_count = 0
        books_found = set()
        
        # Pattern: "BookName Chapter:Verse\tVerse text"
        verse_pattern = re.compile(r'^([A-Za-z0-9\s]+)\s+(\d+):(\d+)\t(.+)$')
        
        # Book name mapping to canonical IDs
        book_mapping = {
            'Genesis': 'Gen', 'Exodus': 'Exod', 'Leviticus': 'Lev', 'Numbers': 'Num', 'Deuteronomy': 'Deut',
            'Joshua': 'Josh', 'Judges': 'Judg', 'Ruth': 'Ruth', 
            '1 Samuel': '1Sam', '2 Samuel': '2Sam', '1 Kings': '1Kgs', '2 Kings': '2Kgs',
            '1 Chronicles': '1Chr', '2 Chronicles': '2Chr', 'Ezra': 'Ezra', 'Nehemiah': 'Neh', 
            'Esther': 'Esth', 'Job': 'Job', 'Psalms': 'Ps', 'Psalm': 'Ps', 'Proverbs': 'Prov', 
            'Ecclesiastes': 'Eccl', 'Song of Solomon': 'Song', 'Isaiah': 'Isa', 'Jeremiah': 'Jer',
            'Lamentations': 'Lam', 'Ezekiel': 'Ezek', 'Daniel': 'Dan', 'Hosea': 'Hos',
            'Joel': 'Joel', 'Amos': 'Amos', 'Obadiah': 'Obad', 'Jonah': 'Jonah', 
            'Micah': 'Mic', 'Nahum': 'Nah', 'Habakkuk': 'Hab', 'Zephaniah': 'Zeph',
            'Haggai': 'Hag', 'Zechariah': 'Zech', 'Malachi': 'Mal',
            'Matthew': 'Matt', 'Mark': 'Mark', 'Luke': 'Luke', 'John': 'John', 'Acts': 'Acts',
            'Romans': 'Rom', '1 Corinthians': '1Cor', '2 Corinthians': '2Cor', 'Galatians': 'Gal',
            'Ephesians': 'Eph', 'Philippians': 'Phil', 'Colossians': 'Col', 
            '1 Thessalonians': '1Thess', '2 Thessalonians': '2Thess', 
            '1 Timothy': '1Tim', '2 Timothy': '2Tim', 'Titus': 'Titus', 'Philemon': 'Phlm',
            'Hebrews': 'Heb', 'James': 'Jas', '1 Peter': '1Pet', '2 Peter': '2Pet',
            '1 John': '1John', '2 John': '2John', '3 John': '3John', 'Jude': 'Jude', 
            'Revelation': 'Rev'
        }
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Skip header lines
            if not line or line == 'KJV' or 'King James Bible' in line:
                continue
            
            # Parse verse
            match = verse_pattern.match(line)
            if match:
                book_name = match.group(1).strip()
                chapter_num = int(match.group(2))
                verse_num = int(match.group(3))
                verse_text = match.group(4).strip()
                
                # Map to canonical book ID
                if book_name not in book_mapping:
                    print(f"   ⚠️  Unknown book: '{book_name}' on line {line_num + 1}")
                    continue
                
                book_id = book_mapping[book_name]
                books_found.add(book_id)
                
                # Normalize text
                normalized_text = self.normalizer.normalize_text(verse_text)
                
                # Store verse
                verses_data[book_id][chapter_num][verse_num] = normalized_text
                verse_count += 1
                
                if verse_count % 5000 == 0:
                    print(f"   ⚡ Processed {verse_count:,} verses...")
            else:
                if line.strip():  # Only warn about non-empty unmatched lines
                    print(f"   ⚠️  Unmatched line {line_num + 1}: {line[:50]}...")
        
        books_list = sorted(books_found)
        print(f"   ✅ Processed {verse_count:,} verses from {len(books_list)} books")
        print(f"   📚 Books found: {', '.join(books_list)}")
        
        report["stages"]["stage_1"] = {
            "name": "Clean Format Parsing",
            "verses_processed": verse_count,
            "books_found": len(books_list),
            "books_list": books_list,
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
        print(f"   💡 Warnings: {validation_report['summary']['warning_count']}")
        
        # Show recommendations  
        for rec in validation_report['recommendations']:
            if '✅' in rec:
                print(f"   {rec}")
            elif 'CRITICAL' in rec or '❌' in rec:
                print(f"   🚨 {rec}")
            else:
                print(f"   💡 {rec}")
        
        # Show details if not perfect
        if validation_report['summary']['error_count'] > 0:
            print(f"\n🔍 Validation Issues:")
            if validation_report['missing_content']['books']:
                print(f"   Missing books: {validation_report['missing_content']['books']}")
            if validation_report['missing_content']['verses']:
                sample_missing = validation_report['missing_content']['verses'][:5]
                print(f"   Sample missing verses: {[v['osis_id'] for v in sample_missing]}")
        
        report["stages"]["stage_2"] = {
            "name": "Canonical Validation",
            "coverage_percentage": validation_report['summary']['coverage_percentage'],
            "is_valid": validation_report['summary']['is_valid'],
            "error_count": validation_report['summary']['error_count'],
            "warning_count": validation_report['summary']['warning_count'],
            "validation_report": validation_report,
            "time_seconds": time.time() - stage_start
        }
        
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
        
        total_books = len(verses_data)
        processed_books = 0
        
        for book_id, chapters in verses_data.items():
            processed_books += 1
            print(f"   📖 Chunking {book_id} ({processed_books}/{total_books})")
            
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
                
                # Pericope chunks (Layer B) - overlapping windows
                verse_list = sorted(verses.items())
                window_size = 6
                stride = 3
                
                for i in range(0, len(verse_list), stride):
                    window_verses = verse_list[i:i + window_size]
                    if len(window_verses) < 3:  # Minimum pericope size
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
                            "window_size": len(window_verses),
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
        print(f"      📝 {verse_count:,} verse chunks (Layer A)")
        print(f"      📖 {pericope_count:,} pericope chunks (Layer B)")
        print(f"      📚 {chapter_count:,} chapter chunks (Layer C)")
        
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
        pericope_chunks = len(hierarchical_chunks["pericopes"])
        chapter_chunks = len(hierarchical_chunks["chapters"])
        
        # Expected metrics
        expected_verses = 31102
        coverage_quality = (verse_chunks / expected_verses) * 100
        pericope_ratio = pericope_chunks / verse_chunks if verse_chunks > 0 else 0
        chapter_ratio = chapter_chunks / verse_chunks if verse_chunks > 0 else 0
        
        print(f"   📊 Quality Metrics:")
        print(f"      Coverage: {coverage_quality:.2f}% ({verse_chunks:,}/{expected_verses:,})")
        print(f"      Pericope ratio: {pericope_ratio:.3f}")
        print(f"      Chapter ratio: {chapter_ratio:.3f}")
        print(f"      Total chunks: {total_chunks:,}")
        
        # Quality scoring
        quality_score = 0
        max_score = 5
        
        if coverage_quality >= 99.9:
            quality_score += 2
            print(f"      ✅ Perfect coverage: +2")
        elif coverage_quality >= 99:
            quality_score += 1
            print(f"      ✅ Excellent coverage: +1")
        
        if 0.30 <= pericope_ratio <= 0.35:
            quality_score += 1
            print(f"      ✅ Optimal pericope ratio: +1")
        
        if 0.03 <= chapter_ratio <= 0.04:
            quality_score += 1
            print(f"      ✅ Good chapter ratio: +1")
        
        if total_chunks >= 40000:
            quality_score += 1
            print(f"      ✅ Rich hierarchical data: +1")
        
        print(f"   🏆 Final Quality Score: {quality_score}/{max_score}")
        
        if quality_score >= 4:
            print(f"   🎉 EXCELLENT QUALITY - Ready for embeddings!")
        elif quality_score >= 3:
            print(f"   ✅ GOOD QUALITY - Proceed with confidence")
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT")
        
        report["stages"]["stage_5"] = {
            "name": "Quality Assessment",
            "quality_score": quality_score,
            "max_score": max_score,
            "coverage_quality": coverage_quality,
            "pericope_ratio": pericope_ratio,
            "chapter_ratio": chapter_ratio,
            "total_chunks": total_chunks,
            "time_seconds": time.time() - stage_start
        }


if __name__ == "__main__":
    ingestor = CleanKJVIngestor()
    
    kjv_path = "/home/nigel/Downloads/KJV.txt"
    report = ingestor.ingest_kjv_bible(kjv_path, "kjv")
    
    # Save report
    with open("domains/theology/processed/kjv_clean_ingestion_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Report saved to: domains/theology/processed/kjv_clean_ingestion_report.json")