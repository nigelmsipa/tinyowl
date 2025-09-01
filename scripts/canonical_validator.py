#!/usr/bin/env python3
"""
TinyOwl Canonical Validation System
Implements bulletproof verse count validation and coverage testing
"""

import yaml
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from text_normalizer import TextNormalizer


@dataclass
class ValidationResult:
    """Results of canonical validation"""
    is_valid: bool
    total_verses: int
    expected_verses: int
    missing_books: List[str]
    missing_chapters: List[Dict]
    missing_verses: List[Dict]
    extra_verses: List[Dict]
    duplicate_osis_ids: List[str]
    errors: List[str]
    warnings: List[str]


class CanonicalValidator:
    """Validates Bible text against canonical standards"""
    
    def __init__(self, config_path: str = "configs/osis_canonical.yaml"):
        self.normalizer = TextNormalizer(config_path)
        self.config = self.normalizer.config
        self._build_canonical_structure()
    
    def _build_canonical_structure(self):
        """Build canonical reference structure"""
        self.canonical_books = {}
        self.expected_osis_ids = set()
        
        # Process Old Testament
        for book in self.config['canonical_books']['old_testament']:
            book_id = book['id']
            self.canonical_books[book_id] = {
                'testament': 'Old',
                'chapter_count': book['chapter_count'],
                'verse_counts': book['verse_counts']
            }
            
            # Generate expected OSIS IDs
            for chapter in range(1, book['chapter_count'] + 1):
                verse_count = book['verse_counts'][chapter - 1]
                for verse in range(1, verse_count + 1):
                    osis_id = self.normalizer.create_osis_id(book_id, chapter, verse)
                    self.expected_osis_ids.add(osis_id)
        
        # Process New Testament
        for book in self.config['canonical_books']['new_testament']:
            book_id = book['id']
            self.canonical_books[book_id] = {
                'testament': 'New',
                'chapter_count': book['chapter_count'],
                'verse_counts': book['verse_counts']
            }
            
            # Generate expected OSIS IDs
            for chapter in range(1, book['chapter_count'] + 1):
                verse_count = book['verse_counts'][chapter - 1]
                for verse in range(1, verse_count + 1):
                    osis_id = self.normalizer.create_osis_id(book_id, chapter, verse)
                    self.expected_osis_ids.add(osis_id)
    
    def validate_translation(self, verses_data: Dict) -> ValidationResult:
        """
        Validate a complete Bible translation
        
        Args:
            verses_data: Dict with structure {book_id: {chapter: {verse: text}}}
        
        Returns:
            ValidationResult with comprehensive validation details
        """
        result = ValidationResult(
            is_valid=True,
            total_verses=0,
            expected_verses=len(self.expected_osis_ids),
            missing_books=[],
            missing_chapters=[],
            missing_verses=[],
            extra_verses=[],
            duplicate_osis_ids=[],
            errors=[],
            warnings=[]
        )
        
        found_osis_ids = set()
        osis_id_counts = {}
        
        # Check each canonical book
        for book_id, book_config in self.canonical_books.items():
            if book_id not in verses_data:
                result.missing_books.append(book_id)
                result.errors.append(f"Missing book: {book_id}")
                continue
            
            book_verses = verses_data[book_id]
            expected_chapters = book_config['chapter_count']
            expected_verse_counts = book_config['verse_counts']
            
            # Check each chapter
            for chapter in range(1, expected_chapters + 1):
                if chapter not in book_verses:
                    result.missing_chapters.append({
                        'book': book_id,
                        'chapter': chapter
                    })
                    result.errors.append(f"Missing chapter: {book_id} {chapter}")
                    continue
                
                chapter_verses = book_verses[chapter]
                expected_verses = expected_verse_counts[chapter - 1]
                
                # Check each verse
                for verse in range(1, expected_verses + 1):
                    osis_id = self.normalizer.create_osis_id(book_id, chapter, verse)
                    
                    if verse not in chapter_verses:
                        result.missing_verses.append({
                            'book': book_id,
                            'chapter': chapter,
                            'verse': verse,
                            'osis_id': osis_id
                        })
                        result.errors.append(f"Missing verse: {osis_id}")
                    else:
                        # Track OSIS ID
                        found_osis_ids.add(osis_id)
                        osis_id_counts[osis_id] = osis_id_counts.get(osis_id, 0) + 1
                        result.total_verses += 1
                
                # Check for extra verses in this chapter
                for verse in chapter_verses:
                    if verse > expected_verses:
                        osis_id = self.normalizer.create_osis_id(book_id, chapter, verse)
                        result.extra_verses.append({
                            'book': book_id,
                            'chapter': chapter,
                            'verse': verse,
                            'osis_id': osis_id
                        })
                        result.warnings.append(f"Extra verse: {osis_id}")
        
        # Check for extra books
        for book_id in verses_data:
            if book_id not in self.canonical_books:
                result.warnings.append(f"Extra book found: {book_id}")
        
        # Check for duplicates
        for osis_id, count in osis_id_counts.items():
            if count > 1:
                result.duplicate_osis_ids.append(osis_id)
                result.errors.append(f"Duplicate OSIS ID: {osis_id} (found {count} times)")
        
        # Final validation
        missing_count = len(self.expected_osis_ids - found_osis_ids)
        if missing_count > 0:
            result.errors.append(f"Missing {missing_count} verses total")
        
        extra_count = len(found_osis_ids - self.expected_osis_ids)
        if extra_count > 0:
            result.warnings.append(f"Found {extra_count} extra verses")
        
        # Set overall validity
        result.is_valid = (
            len(result.errors) == 0 and
            result.total_verses == result.expected_verses and
            len(result.missing_books) == 0
        )
        
        return result
    
    def validate_osis_id_format(self, osis_id: str) -> bool:
        """Validate OSIS ID format"""
        pattern = self.config['validation']['osis_id_pattern']
        import re
        return bool(re.match(pattern, osis_id))
    
    def get_canonical_reference(self, book_id: str, chapter: int, verse: int) -> Optional[str]:
        """Get canonical reference string for display"""
        if book_id not in self.canonical_books:
            return None
        
        # Find full book name
        full_name = None
        for testament in ['old_testament', 'new_testament']:
            for book in self.config['canonical_books'][testament]:
                if book['id'] == book_id:
                    full_name = book['full_name']
                    break
            if full_name:
                break
        
        if not full_name:
            return None
        
        return f"{full_name} {chapter}:{verse}"
    
    def run_comprehensive_validation(self, verses_data: Dict) -> Dict:
        """Run all validation checks and return comprehensive report"""
        validation = self.validate_translation(verses_data)
        
        report = {
            'summary': {
                'is_valid': validation.is_valid,
                'total_verses_found': validation.total_verses,
                'total_verses_expected': validation.expected_verses,
                'coverage_percentage': (validation.total_verses / validation.expected_verses) * 100,
                'error_count': len(validation.errors),
                'warning_count': len(validation.warnings)
            },
            'missing_content': {
                'books': validation.missing_books,
                'chapters': validation.missing_chapters,
                'verses': validation.missing_verses
            },
            'extra_content': {
                'verses': validation.extra_verses
            },
            'quality_issues': {
                'duplicates': validation.duplicate_osis_ids
            },
            'errors': validation.errors,
            'warnings': validation.warnings,
            'recommendations': self._generate_recommendations(validation)
        }
        
        return report
    
    def _generate_recommendations(self, validation: ValidationResult) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        if validation.missing_books:
            recommendations.append(f"CRITICAL: {len(validation.missing_books)} missing books. Complete Bible text required.")
        
        if validation.missing_verses:
            recommendations.append(f"CRITICAL: {len(validation.missing_verses)} missing verses. Check source text quality.")
        
        if validation.duplicate_osis_ids:
            recommendations.append(f"ERROR: {len(validation.duplicate_osis_ids)} duplicate verses. Clean source text.")
        
        if validation.extra_verses:
            recommendations.append(f"WARNING: {len(validation.extra_verses)} extra verses. Verify source accuracy.")
        
        coverage = (validation.total_verses / validation.expected_verses) * 100
        if coverage < 100:
            recommendations.append(f"Coverage at {coverage:.2f}%. Aim for 100% before embedding.")
        
        if validation.is_valid:
            recommendations.append("✅ Validation passed! Ready for hierarchical chunking.")
        else:
            recommendations.append("❌ Fix all CRITICAL errors before proceeding to embedding.")
        
        return recommendations


def create_test_validation():
    """Create test data for validation system"""
    validator = CanonicalValidator()
    
    # Test with minimal data
    test_data = {
        'Gen': {
            1: {1: "In the beginning God created the heaven and the earth."},
            2: {1: "Thus the heavens and the earth were finished."}
        }
    }
    
    report = validator.run_comprehensive_validation(test_data)
    return report


if __name__ == "__main__":
    # Test the validator
    print("Testing Canonical Validator...")
    
    test_report = create_test_validation()
    
    print(f"Validation Summary:")
    print(f"- Valid: {test_report['summary']['is_valid']}")
    print(f"- Coverage: {test_report['summary']['coverage_percentage']:.2f}%")
    print(f"- Errors: {test_report['summary']['error_count']}")
    print(f"- Warnings: {test_report['summary']['warning_count']}")
    
    print(f"\nRecommendations:")
    for rec in test_report['recommendations']:
        print(f"  {rec}")