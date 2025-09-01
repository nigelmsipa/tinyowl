#!/usr/bin/env python3
"""
TinyOwl Bulletproof Ingestion Pipeline
Integrates all foundation components for high-quality Bible text processing
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Import our bulletproof components
from text_normalizer import TextNormalizer
from canonical_validator import CanonicalValidator
from scripture_extractor import ScriptureExtractor
from evaluation_harness import EvaluationHarness

class BulletproofIngestor:
    """Main ingestion pipeline with bulletproof quality control"""
    
    def __init__(self, output_dir: str = "domains/theology"):
        self.output_dir = Path(output_dir)
        self.normalizer = TextNormalizer()
        self.validator = CanonicalValidator()
        self.scripture_extractor = ScriptureExtractor()
        self.harness = EvaluationHarness()
        
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "chunks").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
        
    def ingest_kjv_bible(self, filepath: str, translation_id: str = "kjv") -> Dict[str, Any]:
        """
        Complete bulletproof ingestion of KJV Bible text
        
        Args:
            filepath: Path to KJV text file
            translation_id: Translation identifier (kjv)
        
        Returns:
            Ingestion report with quality metrics
        """
        print("🚀 Starting Bulletproof KJV Ingestion Pipeline")
        print("=" * 60)
        
        start_time = time.time()
        report = {
            "translation_id": translation_id,
            "source_file": filepath,
            "start_time": start_time,
            "stages": {}
        }
        
        try:
            # Stage 1: Load and normalize text
            verses_data = self._stage_1_normalize_text(filepath, translation_id, report)
            
            # Stage 2: Assign OSIS IDs and validate
            validated_data = self._stage_2_validate_coverage(verses_data, translation_id, report)
            
            # Stage 3: Create hierarchical chunks
            hierarchical_chunks = self._stage_3_create_hierarchical_chunks(validated_data, translation_id, report)
            
            # Stage 4: Save processed data
            self._stage_4_save_chunks(hierarchical_chunks, translation_id, report)
            
            # Stage 5: Quality assessment
            self._stage_5_quality_assessment(hierarchical_chunks, translation_id, report)
            
        except Exception as e:
            print(f"❌ PIPELINE FAILED: {e}")
            report["success"] = False
            report["error"] = str(e)
            return report
        
        # Success!
        report["success"] = True
        report["total_time"] = time.time() - start_time
        report["end_time"] = time.time()
        
        print("\n🎉 BULLETPROOF INGESTION COMPLETE!")
        print(f"⏱️  Total time: {report['total_time']:.2f} seconds")
        
        return report
    
    def _stage_1_normalize_text(self, filepath: str, translation_id: str, report: Dict) -> Dict[str, Dict[int, Dict[int, str]]]:
        """Stage 1: Load and normalize text with OSIS ID assignment"""
        print("\n📝 Stage 1: Text Normalization & OSIS Assignment")
        stage_start = time.time()
        
        # Load file with correct encoding
        with open(filepath, 'r', encoding='latin1') as f:
            raw_lines = f.readlines()
        
        print(f"   📖 Loaded {len(raw_lines):,} lines")
        
        # Parse Bible structure
        verses_data = defaultdict(lambda: defaultdict(dict))
        current_book_id = None
        current_chapter = None
        
        # Patterns for parsing
        chapter_pattern = re.compile(r'^CHAPTER\s+(\d+)', re.IGNORECASE)
        verse_pattern = re.compile(r'^\s*(\d+)\s+(.+)$')
        
        # Book detection patterns - handle the full KJV structure
        book_patterns = [
            (r'THE FIRST BOOK OF MOSES, CALLED\s*GENESIS', 'Gen'),
            (r'THE SECOND BOOK OF MOSES, CALLED\s*EXODUS', 'Exod'), 
            (r'THE THIRD BOOK OF MOSES, CALLED\s*LEVITICUS', 'Lev'),
            (r'THE FOURTH BOOK OF MOSES, CALLED\s*NUMBERS', 'Num'),
            (r'THE FIFTH BOOK OF MOSES, CALLED\s*DEUTERONOMY', 'Deut'),
            (r'THE BOOK OF\s*JOSHUA', 'Josh'),
            (r'THE BOOK OF\s*JUDGES', 'Judg'),
            (r'THE BOOK OF\s*RUTH', 'Ruth'),
            (r'THE FIRST BOOK OF\s*SAMUEL', '1Sam'),
            (r'THE SECOND BOOK OF\s*SAMUEL', '2Sam'),
            (r'THE FIRST BOOK OF THE KINGS', '1Kgs'),
            (r'THE SECOND BOOK OF THE KINGS', '2Kgs'),
            (r'THE FIRST BOOK OF THE CHRONICLES', '1Chr'),
            (r'THE SECOND BOOK OF THE CHRONICLES', '2Chr'),
            (r'EZRA', 'Ezra'),
            (r'THE BOOK OF\s*NEHEMIAH', 'Neh'),
            (r'THE BOOK OF\s*ESTHER', 'Esth'),
            (r'THE BOOK OF\s*JOB', 'Job'),
            (r'THE BOOK OF\s*PSALMS', 'Ps'),
            (r'THE PROVERBS OF SOLOMON', 'Prov'),
            (r'ECCLESIASTES', 'Eccl'),
            (r'THE SONG OF SOLOMON', 'Song'),
            (r'THE BOOK OF THE PROPHET\s*ISAIAH', 'Isa'),
            (r'THE BOOK OF THE PROPHET\s*JEREMIAH', 'Jer'),
            (r'THE LAMENTATIONS OF JEREMIAH', 'Lam'),
            (r'THE BOOK OF THE PROPHET\s*EZEKIEL', 'Ezek'),
            (r'THE BOOK OF\s*DANIEL', 'Dan'),
            (r'HOSEA', 'Hos'),
            (r'JOEL', 'Joel'),
            (r'AMOS', 'Amos'),
            (r'OBADIAH', 'Obad'),
            (r'JONAH', 'Jonah'),
            (r'MICAH', 'Mic'),
            (r'NAHUM', 'Nah'),
            (r'HABAKKUK', 'Hab'),
            (r'ZEPHANIAH', 'Zeph'),
            (r'HAGGAI', 'Hag'),
            (r'ZECHARIAH', 'Zech'),
            (r'MALACHI', 'Mal'),
            (r'THE GOSPEL ACCORDING TO\s*SAINT MATTHEW', 'Matt'),
            (r'THE GOSPEL ACCORDING TO\s*SAINT MARK', 'Mark'),
            (r'THE GOSPEL ACCORDING TO\s*SAINT LUKE', 'Luke'),
            (r'THE GOSPEL ACCORDING TO\s*SAINT JOHN', 'John'),
            (r'THE ACTS OF THE APOSTLES', 'Acts'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*ROMANS', 'Rom'),
            (r'THE FIRST EPISTLE OF PAUL THE APOSTLE TO THE\s*CORINTHIANS', '1Cor'),
            (r'THE SECOND EPISTLE OF PAUL THE APOSTLE TO THE\s*CORINTHIANS', '2Cor'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*GALATIANS', 'Gal'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*EPHESIANS', 'Eph'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*PHILIPPIANS', 'Phil'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*COLOSSIANS', 'Col'),
            (r'THE FIRST EPISTLE OF PAUL THE APOSTLE TO THE\s*THESSALONIANS', '1Thess'),
            (r'THE SECOND EPISTLE OF PAUL THE APOSTLE TO THE\s*THESSALONIANS', '2Thess'),
            (r'THE FIRST EPISTLE OF PAUL THE APOSTLE TO\s*TIMOTHY', '1Tim'),
            (r'THE SECOND EPISTLE OF PAUL THE APOSTLE TO\s*TIMOTHY', '2Tim'),
            (r'THE EPISTLE OF PAUL TO\s*TITUS', 'Titus'),
            (r'THE EPISTLE OF PAUL TO\s*PHILEMON', 'Phlm'),
            (r'THE EPISTLE OF PAUL THE APOSTLE TO THE\s*HEBREWS', 'Heb'),
            (r'THE GENERAL EPISTLE OF\s*JAMES', 'Jas'),
            (r'THE FIRST EPISTLE GENERAL OF\s*PETER', '1Pet'),
            (r'THE SECOND EPISTLE GENERAL OF\s*PETER', '2Pet'),
            (r'THE FIRST GENERAL EPISTLE OF\s*JOHN', '1John'),
            (r'THE SECOND EPISTLE OF\s*JOHN', '2John'),
            (r'THE THIRD EPISTLE OF\s*JOHN', '3John'),
            (r'THE GENERAL EPISTLE OF\s*JUDE', 'Jude'),
            (r'THE REVELATION\s*OF SAINT JOHN THE DIVINE', 'Rev')
        ]
        
        # Compile patterns for efficiency
        compiled_book_patterns = [(re.compile(pattern, re.IGNORECASE), book_id) for pattern, book_id in book_patterns]
        
        verse_count = 0
        in_bible_content = False  # Skip table of contents
        
        for line_num, line in enumerate(raw_lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for book patterns (multi-line aware)
            line_with_next = line
            if line_num + 1 < len(raw_lines):
                next_line = raw_lines[line_num + 1].strip()
                line_with_next = f"{line} {next_line}"
            
            book_found = False
            for pattern, book_id in compiled_book_patterns:
                if pattern.search(line_with_next):
                    current_book_id = book_id
                    current_chapter = None
                    in_bible_content = True  # Now we're in actual Bible content
                    print(f"   📖 Processing: {current_book_id}")
                    book_found = True
                    break
            
            if book_found:
                continue
            
            # Only process content after we've found the first book
            if not in_bible_content:
                continue
            
            # Check for chapter markers
            chapter_match = chapter_pattern.match(line)
            if chapter_match and current_book_id:
                current_chapter = int(chapter_match.group(1))
                continue
            
            # Check for verses
            verse_match = verse_pattern.match(line)
            if verse_match and current_book_id and current_chapter:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                # Normalize the text
                normalized_text = self.normalizer.normalize_text(verse_text)
                
                # Store verse
                verses_data[current_book_id][current_chapter][verse_num] = normalized_text
                verse_count += 1
                
                if verse_count % 5000 == 0:
                    print(f"   ⚡ Processed {verse_count:,} verses...")
        
        print(f"   ✅ Normalized {verse_count:,} verses")
        print(f"   📚 Found {len(verses_data)} books")
        
        report["stages"]["stage_1"] = {
            "name": "Text Normalization",
            "verses_processed": verse_count,
            "books_found": len(verses_data),
            "time_seconds": time.time() - stage_start
        }
        
        return verses_data
    
    def _stage_2_validate_coverage(self, verses_data: Dict, translation_id: str, report: Dict) -> Dict:
        """Stage 2: Validate canonical coverage"""
        print("\n🔍 Stage 2: Canonical Coverage Validation")
        stage_start = time.time()
        
        # Run comprehensive validation
        validation_report = self.validator.run_comprehensive_validation(verses_data)
        
        print(f"   📊 Coverage: {validation_report['summary']['coverage_percentage']:.2f}%")
        print(f"   ✅ Valid: {validation_report['summary']['is_valid']}")
        print(f"   ⚠️  Errors: {validation_report['summary']['error_count']}")
        print(f"   💡 Warnings: {validation_report['summary']['warning_count']}")
        
        # Print recommendations
        for rec in validation_report['recommendations']:
            if rec.startswith('✅'):
                print(f"   {rec}")
            elif rec.startswith('❌') or rec.startswith('CRITICAL'):
                print(f"   🚨 {rec}")
            else:
                print(f"   💡 {rec}")
        
        # Fail fast if validation fails
        if not validation_report['summary']['is_valid']:
            raise ValueError("Validation failed - fix errors before proceeding")
        
        report["stages"]["stage_2"] = {
            "name": "Canonical Validation",
            "coverage_percentage": validation_report['summary']['coverage_percentage'],
            "is_valid": validation_report['summary']['is_valid'],
            "error_count": validation_report['summary']['error_count'],
            "time_seconds": time.time() - stage_start,
            "validation_report": validation_report
        }
        
        return verses_data
    
    def _stage_3_create_hierarchical_chunks(self, verses_data: Dict, translation_id: str, report: Dict) -> Dict:
        """Stage 3: Create hierarchical chunks (verse/pericope/chapter)"""
        print("\n🏗️  Stage 3: Hierarchical Chunking")
        stage_start = time.time()
        
        hierarchical_chunks = {
            "verses": [],
            "pericopes": [],
            "chapters": []
        }
        
        total_books = len(verses_data)
        book_count = 0
        
        for book_id, chapters in verses_data.items():
            book_count += 1
            print(f"   📖 Chunking {book_id} ({book_count}/{total_books})")
            
            # Create verse-level chunks (Layer A)
            for chapter_num, verses in chapters.items():
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
                
                # Create pericope chunks (Layer B) - overlapping windows
                verse_list = sorted(verses.items())
                window_size = 6
                stride = 3
                
                for i in range(0, len(verse_list), stride):
                    window_verses = verse_list[i:i + window_size]
                    if len(window_verses) < 3:  # Minimum pericope size
                        continue
                    
                    start_verse = window_verses[0][0]
                    end_verse = window_verses[-1][0]
                    
                    # Combine verse texts
                    combined_text = " ".join([verse_text for _, verse_text in window_verses])
                    
                    start_osis = self.normalizer.create_osis_id(book_id, chapter_num, start_verse)
                    end_osis = self.normalizer.create_osis_id(book_id, chapter_num, end_verse)
                    
                    pericope_chunk = {
                        "id": f"{translation_id}_{book_id.lower()}_c{chapter_num:02d}_p{i+1:03d}",
                        "osis_id_start": start_osis,
                        "osis_id_end": end_osis,
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
                
                # Create chapter chunk (Layer C)
                all_verses_text = " ".join([verse_text for _, verse_text in verse_list])
                chapter_osis_start = self.normalizer.create_osis_id(book_id, chapter_num, 1)
                
                chapter_chunk = {
                    "id": f"{translation_id}_{book_id.lower()}_chapter_{chapter_num:02d}",
                    "osis_id_start": chapter_osis_start,
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
        
        # Summary
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
    
    def _stage_4_save_chunks(self, hierarchical_chunks: Dict, translation_id: str, report: Dict) -> None:
        """Stage 4: Save all chunk layers"""
        print("\n💾 Stage 4: Saving Hierarchical Chunks")
        stage_start = time.time()
        
        # Save each layer separately
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
    
    def _stage_5_quality_assessment(self, hierarchical_chunks: Dict, translation_id: str, report: Dict) -> None:
        """Stage 5: Final quality assessment"""
        print("\n🏆 Stage 5: Quality Assessment") 
        stage_start = time.time()
        
        # Calculate quality metrics
        total_chunks = sum(len(chunks) for chunks in hierarchical_chunks.values())
        verse_chunks = len(hierarchical_chunks["verses"])
        
        # Expected totals for KJV
        expected_verses = 31102
        coverage_quality = (verse_chunks / expected_verses) * 100
        
        # Assess chunk distribution
        pericope_ratio = len(hierarchical_chunks["pericopes"]) / verse_chunks
        chapter_ratio = len(hierarchical_chunks["chapters"]) / verse_chunks
        
        print(f"   📊 Quality Metrics:")
        print(f"      Coverage: {coverage_quality:.2f}% ({verse_chunks}/{expected_verses})")
        print(f"      Pericope ratio: {pericope_ratio:.3f}")
        print(f"      Chapter ratio: {chapter_ratio:.3f}")
        print(f"      Total chunks: {total_chunks:,}")
        
        # Quality score
        quality_score = 0
        
        if coverage_quality >= 99.5:
            quality_score += 2
            print(f"      ✅ Excellent coverage: +2")
        elif coverage_quality >= 95:
            quality_score += 1
            print(f"      ✅ Good coverage: +1")
        
        if 0.3 <= pericope_ratio <= 0.4:
            quality_score += 1
            print(f"      ✅ Good pericope ratio: +1")
        
        if 0.03 <= chapter_ratio <= 0.05:
            quality_score += 1 
            print(f"      ✅ Good chapter ratio: +1")
        
        if total_chunks >= 40000:
            quality_score += 1
            print(f"      ✅ Rich hierarchical data: +1")
        
        print(f"   🏆 Final Quality Score: {quality_score}/5")
        
        if quality_score >= 4:
            print(f"   🎉 EXCELLENT QUALITY - Ready for embedding!")
        elif quality_score >= 3:
            print(f"   ✅ GOOD QUALITY - Proceed with confidence")
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT")
        
        report["stages"]["stage_5"] = {
            "name": "Quality Assessment",
            "quality_score": quality_score,
            "coverage_quality": coverage_quality,
            "pericope_ratio": pericope_ratio,
            "chapter_ratio": chapter_ratio,
            "total_chunks": total_chunks,
            "time_seconds": time.time() - stage_start
        }


if __name__ == "__main__":
    # Initialize bulletproof ingestor
    ingestor = BulletproofIngestor()
    
    # Process KJV
    kjv_path = "/home/nigel/Downloads/TheHolyBibleKJV.txt"
    report = ingestor.ingest_kjv_bible(kjv_path, "kjv")
    
    # Save report
    with open("domains/theology/processed/kjv_ingestion_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Full report saved to: domains/theology/processed/kjv_ingestion_report.json")