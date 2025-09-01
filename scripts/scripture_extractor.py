#!/usr/bin/env python3
"""
TinyOwl Scripture Reference Extractor
Bulletproof extraction and normalization of Bible references from sermons
"""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from text_normalizer import TextNormalizer


@dataclass
class ScriptureReference:
    """Standardized scripture reference"""
    osis_id_start: str
    osis_id_end: Optional[str]
    book_id: str
    chapter_start: int
    verse_start: int
    chapter_end: Optional[int]
    verse_end: Optional[int]
    original_text: str
    confidence: float
    range_type: str  # 'single', 'verse_range', 'chapter_range', 'multi_chapter'


class ScriptureExtractor:
    """Extract and normalize scripture references from text"""
    
    def __init__(self, config_path: str = "configs/osis_canonical.yaml"):
        self.normalizer = TextNormalizer(config_path)
        self._build_comprehensive_patterns()
        self._load_book_mappings()
    
    def _load_book_mappings(self):
        """Load comprehensive book name mappings"""
        self.book_aliases = self.normalizer.book_aliases
        
        # Add additional sermon-specific variations
        additional_aliases = {
            # Common abbreviated forms
            "1st Samuel": "1Sam",
            "2nd Samuel": "2Sam",
            "1st Kings": "1Kgs",
            "2nd Kings": "2Kgs",
            "1st Chronicles": "1Chr",
            "2nd Chronicles": "2Chr",
            "1st Corinthians": "1Cor",
            "2nd Corinthians": "2Cor",
            "1st Thessalonians": "1Thess",
            "2nd Thessalonians": "2Thess",
            "1st Timothy": "1Tim",
            "2nd Timothy": "2Tim",
            "1st Peter": "1Pet",
            "2nd Peter": "2Pet",
            "1st John": "1John",
            "2nd John": "2John",
            "3rd John": "3John",
            
            # Spoken variations
            "First Samuel": "1Sam",
            "Second Samuel": "2Sam",
            "Saint Matthew": "Matt",
            "Saint Mark": "Mark",
            "Saint Luke": "Luke",
            "Saint John": "John",
            "The Gospel of Matthew": "Matt",
            "The Gospel of Mark": "Mark",
            "The Gospel of Luke": "Luke",
            "The Gospel of John": "John",
            "Book of Genesis": "Gen",
            "Book of Revelation": "Rev",
            "The Revelation": "Rev",
            "Revelations": "Rev",  # Common mistake
            
            # Numeric variations
            "I Samuel": "1Sam",
            "II Samuel": "2Sam",
            "I Kings": "1Kgs",
            "II Kings": "2Kgs",
            "I Chronicles": "1Chr",
            "II Chronicles": "2Chr",
            "I Corinthians": "1Cor",
            "II Corinthians": "2Cor",
            "I Thessalonians": "1Thess",
            "II Thessalonians": "2Thess",
            "I Timothy": "1Tim",
            "II Timothy": "2Tim",
            "I Peter": "1Pet",
            "II Peter": "2Pet",
            "I John": "1John",
            "II John": "2John",
            "III John": "3John",
        }
        
        self.book_aliases.update(additional_aliases)
    
    def _build_comprehensive_patterns(self):
        """Build comprehensive regex patterns for scripture references"""
        
        # Book name pattern - handles numbers, spaces, periods
        book_pattern = r'(?:\d+\s*)?(?:st|nd|rd|th)?\s*[A-Za-z]+(?:\s+[A-Za-z]+)*'
        
        self.patterns = [
            # Pattern 1: Standard format "Book Chapter:Verse"
            # Examples: "John 3:16", "1 Samuel 15:22", "2 Corinthians 5:17"
            {
                'pattern': re.compile(
                    rf'\b({book_pattern})\s+(\d+):(\d+)(?:-(\d+))?\b',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter', 'verse_start', 'verse_end'],
                'type': 'standard'
            },
            
            # Pattern 2: Cross-chapter range "Book Ch:V-Ch:V"
            # Examples: "Luke 15:11-16:8", "Matthew 5:1-7:29"
            {
                'pattern': re.compile(
                    rf'\b({book_pattern})\s+(\d+):(\d+)-(\d+):(\d+)\b',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter_start', 'verse_start', 'chapter_end', 'verse_end'],
                'type': 'cross_chapter'
            },
            
            # Pattern 3: Chapter-only reference "Book Chapter"
            # Examples: "Genesis 1", "Revelation 22", "Psalm 23"
            {
                'pattern': re.compile(
                    rf'\b({book_pattern})\s+(?:chapter\s+)?(\d+)\b(?!\s*:)',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter'],
                'type': 'chapter'
            },
            
            # Pattern 4: Multiple verses "Book Ch:V, V, V"
            # Examples: "Romans 3:23, 24, 25", "John 14:1, 2, 3"
            {
                'pattern': re.compile(
                    rf'\b({book_pattern})\s+(\d+):(\d+)(?:\s*,\s*(\d+))*\b',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter', 'verse_start', 'additional_verses'],
                'type': 'multiple_verses'
            },
            
            # Pattern 5: Contextual references (in context)
            # Examples: "in verse 16", "see verse 23", "as we read in verse 5"
            {
                'pattern': re.compile(
                    r'\b(?:in\s+|see\s+|read\s+in\s+)?verse\s+(\d+)\b',
                    re.IGNORECASE
                ),
                'groups': ['verse'],
                'type': 'contextual'
            },
            
            # Pattern 6: Book with "the" prefix
            # Examples: "the Gospel of John 3:16", "the Book of Genesis 1:1"
            {
                'pattern': re.compile(
                    rf'\b(?:the\s+(?:gospel\s+of\s+|book\s+of\s+)?)({book_pattern})\s+(\d+):(\d+)(?:-(\d+))?\b',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter', 'verse_start', 'verse_end'],
                'type': 'prefixed'
            },
            
            # Pattern 7: Abbreviated with periods
            # Examples: "Gen. 1:1", "Matt. 5:3-12", "1 Sam. 15:22"
            {
                'pattern': re.compile(
                    rf'\b(\d*\s*[A-Za-z]+\.)\s+(\d+):(\d+)(?:-(\d+))?\b',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter', 'verse_start', 'verse_end'],
                'type': 'abbreviated'
            },
            
            # Pattern 8: Parenthetical references
            # Examples: "(John 3:16)", "(see Romans 8:28)", "(cf. Matthew 5:3)"
            {
                'pattern': re.compile(
                    rf'\(\s*(?:see\s+|cf\.\s+)?({book_pattern})\s+(\d+):(\d+)(?:-(\d+))?\s*\)',
                    re.IGNORECASE
                ),
                'groups': ['book', 'chapter', 'verse_start', 'verse_end'],
                'type': 'parenthetical'
            }
        ]
    
    def extract_references(self, text: str, context_book: str = None, context_chapter: int = None) -> List[ScriptureReference]:
        """
        Extract all scripture references from text
        
        Args:
            text: Text to search for references
            context_book: Current book context (for contextual refs)
            context_chapter: Current chapter context (for contextual refs)
        
        Returns:
            List of normalized ScriptureReference objects
        """
        references = []
        text_normalized = self.normalizer.normalize_text(text)
        
        for pattern_config in self.patterns:
            pattern = pattern_config['pattern']
            groups = pattern_config['groups']
            ref_type = pattern_config['type']
            
            for match in pattern.finditer(text_normalized):
                try:
                    ref = self._parse_match(match, groups, ref_type, context_book, context_chapter)
                    if ref:
                        references.append(ref)
                except Exception as e:
                    # Log but don't fail on parsing errors
                    print(f"Warning: Failed to parse reference '{match.group(0)}': {e}")
                    continue
        
        # Remove duplicates and sort
        references = self._deduplicate_references(references)
        return references
    
    def _parse_match(self, match: re.Match, groups: List[str], ref_type: str, 
                    context_book: str = None, context_chapter: int = None) -> Optional[ScriptureReference]:
        """Parse a regex match into a ScriptureReference"""
        
        # Extract matched groups
        group_values = {}
        for i, group_name in enumerate(groups):
            if i < len(match.groups()) and match.group(i + 1):
                group_values[group_name] = match.group(i + 1)
        
        # Handle different reference types
        if ref_type == 'contextual':
            # Need context to resolve
            if not context_book or not context_chapter:
                return None
            
            verse = int(group_values['verse'])
            book_id = self._normalize_book_name(context_book)
            if not book_id:
                return None
            
            return ScriptureReference(
                osis_id_start=self.normalizer.create_osis_id(book_id, context_chapter, verse),
                osis_id_end=None,
                book_id=book_id,
                chapter_start=context_chapter,
                verse_start=verse,
                chapter_end=None,
                verse_end=None,
                original_text=match.group(0),
                confidence=0.8,  # Lower confidence for contextual
                range_type='single'
            )
        
        # All other types need a book name
        if 'book' not in group_values:
            return None
        
        book_id = self._normalize_book_name(group_values['book'])
        if not book_id:
            return None
        
        # Parse chapter and verses
        chapter_start = int(group_values.get('chapter', group_values.get('chapter_start', 0)))
        if chapter_start == 0:
            return None
        
        # Handle different reference patterns
        if ref_type == 'chapter':
            # Chapter-only reference
            return ScriptureReference(
                osis_id_start=self.normalizer.create_osis_id(book_id, chapter_start, 1),
                osis_id_end=None,
                book_id=book_id,
                chapter_start=chapter_start,
                verse_start=1,
                chapter_end=None,
                verse_end=None,
                original_text=match.group(0),
                confidence=0.9,
                range_type='chapter'
            )
        
        elif ref_type == 'cross_chapter':
            # Cross-chapter range
            chapter_end = int(group_values['chapter_end'])
            verse_start = int(group_values['verse_start'])
            verse_end = int(group_values['verse_end'])
            
            return ScriptureReference(
                osis_id_start=self.normalizer.create_osis_id(book_id, chapter_start, verse_start),
                osis_id_end=self.normalizer.create_osis_id(book_id, chapter_end, verse_end),
                book_id=book_id,
                chapter_start=chapter_start,
                verse_start=verse_start,
                chapter_end=chapter_end,
                verse_end=verse_end,
                original_text=match.group(0),
                confidence=0.95,
                range_type='multi_chapter'
            )
        
        else:
            # Standard single verse or verse range
            verse_start = int(group_values.get('verse_start', group_values.get('verse', 1)))
            verse_end = None
            
            if 'verse_end' in group_values and group_values['verse_end']:
                verse_end = int(group_values['verse_end'])
            
            osis_id_start = self.normalizer.create_osis_id(book_id, chapter_start, verse_start)
            osis_id_end = None
            range_type = 'single'
            
            if verse_end:
                osis_id_end = self.normalizer.create_osis_id(book_id, chapter_start, verse_end)
                range_type = 'verse_range'
            
            return ScriptureReference(
                osis_id_start=osis_id_start,
                osis_id_end=osis_id_end,
                book_id=book_id,
                chapter_start=chapter_start,
                verse_start=verse_start,
                chapter_end=None,
                verse_end=verse_end,
                original_text=match.group(0),
                confidence=0.95,
                range_type=range_type
            )
    
    def _normalize_book_name(self, book_name: str) -> Optional[str]:
        """Normalize book name using comprehensive alias mapping"""
        # Clean the book name
        book_clean = book_name.strip().replace('.', '').replace(',', '')
        
        # Direct lookup
        if book_clean in self.book_aliases:
            return self.book_aliases[book_clean]
        
        # Case-insensitive lookup
        for alias, canonical in self.book_aliases.items():
            if alias.lower() == book_clean.lower():
                return canonical
        
        # Partial matching for complex cases
        book_words = book_clean.lower().split()
        for alias, canonical in self.book_aliases.items():
            alias_words = alias.lower().split()
            if len(book_words) >= len(alias_words):
                if all(book_word.startswith(alias_word[:3]) for book_word, alias_word in zip(book_words, alias_words)):
                    return canonical
        
        return None
    
    def _deduplicate_references(self, references: List[ScriptureReference]) -> List[ScriptureReference]:
        """Remove duplicate references and keep highest confidence"""
        seen = {}
        
        for ref in references:
            key = (ref.osis_id_start, ref.osis_id_end)
            
            if key not in seen or ref.confidence > seen[key].confidence:
                seen[key] = ref
        
        # Sort by book order, then chapter, then verse
        return sorted(seen.values(), key=lambda x: (x.book_id, x.chapter_start, x.verse_start))
    
    def extract_and_prelink(self, sermon_text: str, retrieval_function) -> Tuple[List[ScriptureReference], Dict[str, List[str]]]:
        """
        Extract scripture references and pre-compute links to pericopes
        
        Args:
            sermon_text: Sermon content
            retrieval_function: Function to search pericope collection
        
        Returns:
            Tuple of (references, {chunk_id: [pericope_ids]})
        """
        references = self.extract_references(sermon_text)
        prelinks = {}
        
        for ref in references:
            # Search for related pericopes
            search_query = f"{ref.book_id} {ref.chapter_start}:{ref.verse_start}"
            
            try:
                pericope_results = retrieval_function('theology_pericopes', search_query, k=5)
                pericope_ids = [r.get('id', '') for r in pericope_results if r.get('id')]
                
                # Store prelinks using OSIS ID as key
                prelinks[ref.osis_id_start] = pericope_ids
                
            except Exception as e:
                print(f"Warning: Failed to prelink {ref.osis_id_start}: {e}")
                prelinks[ref.osis_id_start] = []
        
        return references, prelinks


def test_scripture_extractor():
    """Test scripture extraction with sample sermon text"""
    extractor = ScriptureExtractor()
    
    test_text = """
    Today we're looking at John 3:16, one of the most beloved verses in Scripture.
    But let's also consider Romans 3:23 and Romans 6:23. In Genesis chapter 1,
    we see God's creative power. The Gospel of Matthew 5:3-12 gives us the Beatitudes.
    As we read in verse 17, Jesus said He came not to destroy but to fulfill.
    Compare this with 1 Samuel 15:22 where obedience is better than sacrifice.
    """
    
    references = extractor.extract_references(test_text)
    
    print(f"Found {len(references)} scripture references:")
    for ref in references:
        print(f"  {ref.original_text} → {ref.osis_id_start}")
        if ref.osis_id_end:
            print(f"    Range: {ref.osis_id_start} to {ref.osis_id_end}")
        print(f"    Confidence: {ref.confidence}, Type: {ref.range_type}")


if __name__ == "__main__":
    test_scripture_extractor()