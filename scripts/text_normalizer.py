#!/usr/bin/env python3
"""
TinyOwl Text Normalization Pipeline
Implements lossless text processing with canonical ID assignment
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path


class TextNormalizer:
    """Handles lossless text normalization and OSIS ID assignment"""
    
    def __init__(self, config_path: str = "configs/osis_canonical.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._compile_patterns()
        
    def _load_config(self) -> Dict:
        """Load OSIS canonical configuration"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        # Book alias patterns
        self.book_aliases = self.config['book_aliases']
        
        # Verse reference patterns
        self.verse_patterns = []
        for pattern_config in self.config['verse_patterns']:
            compiled = re.compile(pattern_config['pattern'], re.IGNORECASE)
            self.verse_patterns.append({
                'pattern': compiled,
                'groups': pattern_config['groups']
            })
        
        # Text cleanup patterns
        self.remove_patterns = []
        for pattern in self.config['text_normalization']['remove_patterns']:
            self.remove_patterns.append(re.compile(pattern, re.MULTILINE | re.IGNORECASE))
    
    def normalize_text(self, text: str) -> str:
        """Apply comprehensive text normalization"""
        # Unicode normalization
        unicode_form = self.config['text_normalization']['unicode_form']
        text = unicodedata.normalize(unicode_form, text)
        
        # Character replacements
        replacements = self.config['text_normalization']['replacements']
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove ornamental patterns
        for pattern in self.remove_patterns:
            text = pattern.sub('', text)
        
        # Whitespace cleanup
        if self.config['text_normalization']['collapse_whitespace']:
            text = re.sub(r'\s+', ' ', text)
        
        if self.config['text_normalization']['strip_leading_trailing']:
            text = text.strip()
        
        return text
    
    def normalize_book_name(self, book_name: str) -> Optional[str]:
        """Normalize book name to canonical OSIS ID"""
        # Direct lookup
        if book_name in self.book_aliases:
            return self.book_aliases[book_name]
        
        # Case-insensitive lookup
        for alias, canonical in self.book_aliases.items():
            if alias.lower() == book_name.lower():
                return canonical
        
        # Partial matching for complex cases like "1 Samuel"
        book_clean = book_name.strip().replace('.', '').replace(',', '')
        for alias, canonical in self.book_aliases.items():
            if alias.lower() == book_clean.lower():
                return canonical
        
        return None
    
    def create_osis_id(self, book_id: str, chapter: int, verse: int) -> str:
        """Create OSIS-style ID: Book.CC.VVV"""
        return f"{book_id}.{chapter:02d}.{verse:03d}"
    
    def parse_verse_reference(self, ref_text: str) -> Optional[Dict]:
        """Parse verse reference into components"""
        for pattern_config in self.verse_patterns:
            match = pattern_config['pattern'].search(ref_text)
            if match:
                groups = pattern_config['groups']
                result = {}
                
                for i, group_name in enumerate(groups):
                    if i < len(match.groups()) and match.group(i + 1):
                        result[group_name] = match.group(i + 1)
                
                # Normalize book name
                if 'book' in result:
                    book_canonical = self.normalize_book_name(result['book'])
                    if book_canonical:
                        result['book_id'] = book_canonical
                    else:
                        return None  # Unknown book
                
                return result
        
        return None
    
    def extract_verse_from_line(self, line: str) -> Optional[Dict]:
        """Extract verse information from a text line"""
        # Common patterns for verse markers in Bible texts
        verse_patterns = [
            r'^(\w+)\s+(\d+):(\d+)\s+(.+)$',  # "Genesis 1:1 In the beginning..."
            r'^(\d+):(\d+)\s+(.+)$',          # "1:1 In the beginning..." (chapter known)
            r'^(\d+)\s+(.+)$',                # "1 In the beginning..." (verse only)
        ]
        
        for pattern in verse_patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                
                if len(groups) == 4:  # Full format: Book Chapter:Verse Text
                    book_id = self.normalize_book_name(groups[0])
                    if book_id:
                        return {
                            'book_id': book_id,
                            'chapter': int(groups[1]),
                            'verse': int(groups[2]),
                            'text': groups[3].strip(),
                            'osis_id': self.create_osis_id(book_id, int(groups[1]), int(groups[2]))
                        }
                elif len(groups) == 3:  # Chapter:Verse Text format
                    return {
                        'chapter': int(groups[0]),
                        'verse': int(groups[1]),
                        'text': groups[2].strip()
                    }
                elif len(groups) == 2:  # Verse Text format
                    return {
                        'verse': int(groups[0]),
                        'text': groups[1].strip()
                    }
        
        return None
    
    def validate_verse_counts(self, processed_verses: Dict[str, Dict]) -> Dict[str, bool]:
        """Validate verse counts against canonical totals"""
        validation_results = {
            'books_present': True,
            'verse_counts_correct': True,
            'total_verses_correct': True,
            'missing_books': [],
            'incorrect_counts': [],
            'details': {}
        }
        
        # Get canonical book definitions
        all_books = []
        all_books.extend(self.config['canonical_books']['old_testament'])
        all_books.extend(self.config['canonical_books']['new_testament'])
        
        total_verses_found = 0
        
        for book_config in all_books:
            book_id = book_config['id']
            expected_chapters = book_config['chapter_count']
            expected_verse_counts = book_config['verse_counts']
            
            if book_id not in processed_verses:
                validation_results['books_present'] = False
                validation_results['missing_books'].append(book_id)
                continue
            
            book_verses = processed_verses[book_id]
            
            # Check chapter count
            actual_chapters = len(book_verses)
            if actual_chapters != expected_chapters:
                validation_results['verse_counts_correct'] = False
                validation_results['incorrect_counts'].append({
                    'book': book_id,
                    'type': 'chapter_count',
                    'expected': expected_chapters,
                    'actual': actual_chapters
                })
            
            # Check verse counts per chapter
            for chapter_num in range(1, expected_chapters + 1):
                expected_verses = expected_verse_counts[chapter_num - 1]
                
                if chapter_num in book_verses:
                    actual_verses = len(book_verses[chapter_num])
                    total_verses_found += actual_verses
                    
                    if actual_verses != expected_verses:
                        validation_results['verse_counts_correct'] = False
                        validation_results['incorrect_counts'].append({
                            'book': book_id,
                            'chapter': chapter_num,
                            'type': 'verse_count',
                            'expected': expected_verses,
                            'actual': actual_verses
                        })
                else:
                    validation_results['verse_counts_correct'] = False
                    validation_results['incorrect_counts'].append({
                        'book': book_id,
                        'chapter': chapter_num,
                        'type': 'missing_chapter',
                        'expected': expected_verses,
                        'actual': 0
                    })
        
        # Check total verse count
        expected_total = self.config['validation']['required_verse_totals']['total']
        if total_verses_found != expected_total:
            validation_results['total_verses_correct'] = False
            validation_results['details']['total_verses'] = {
                'expected': expected_total,
                'actual': total_verses_found,
                'difference': total_verses_found - expected_total
            }
        
        return validation_results


def create_book_alias_map() -> Dict[str, str]:
    """Create comprehensive book alias mapping"""
    aliases = {}
    
    # Old Testament books with common variations
    ot_books = [
        ("Gen", ["Genesis", "Ge", "Gn"]),
        ("Exod", ["Exodus", "Ex", "Exo"]),
        ("Lev", ["Leviticus", "Le", "Lv"]),
        ("Num", ["Numbers", "Nu", "Nm"]),
        ("Deut", ["Deuteronomy", "De", "Dt"]),
        ("Josh", ["Joshua", "Jos"]),
        ("Judg", ["Judges", "Jdg", "Jg"]),
        ("Ruth", ["Ruth", "Ru"]),
        ("1Sam", ["1 Samuel", "1Samuel", "I Samuel", "1Sa", "First Samuel"]),
        ("2Sam", ["2 Samuel", "2Samuel", "II Samuel", "2Sa", "Second Samuel"]),
        ("1Kgs", ["1 Kings", "1Kings", "I Kings", "1Ki", "First Kings"]),
        ("2Kgs", ["2 Kings", "2Kings", "II Kings", "2Ki", "Second Kings"]),
        # ... continue for all books
    ]
    
    # New Testament books
    nt_books = [
        ("Matt", ["Matthew", "Mt", "Mat", "Saint Matthew", "St. Matthew"]),
        ("Mark", ["Mark", "Mk", "Mr", "Saint Mark", "St. Mark"]),
        ("Luke", ["Luke", "Lk", "Lu", "Saint Luke", "St. Luke"]),
        ("John", ["John", "Jn", "Joh", "Saint John", "St. John"]),
        ("Acts", ["Acts", "Ac", "Acts of the Apostles"]),
        ("Rom", ["Romans", "Ro", "Rm"]),
        # ... continue for all NT books
    ]
    
    # Build alias dictionary
    for canonical, alias_list in ot_books + nt_books:
        for alias in alias_list:
            aliases[alias] = canonical
    
    return aliases


if __name__ == "__main__":
    # Test the normalizer
    normalizer = TextNormalizer()
    
    # Test text normalization
    test_text = "Genesis 1:1    In the beginning God created the heaven and the earth."
    normalized = normalizer.normalize_text(test_text)
    print(f"Normalized: {normalized}")
    
    # Test verse parsing
    verse_info = normalizer.extract_verse_from_line(test_text)
    print(f"Parsed: {verse_info}")
    
    # Test OSIS ID creation
    osis_id = normalizer.create_osis_id("Gen", 1, 1)
    print(f"OSIS ID: {osis_id}")