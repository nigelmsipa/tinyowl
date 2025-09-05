#!/usr/bin/env python3
"""
Test Strong's number extraction and improved parsing patterns
"""
import re

def test_strongs_extraction():
    """Test Strong's number extraction from various line formats."""
    
    test_lines = [
        '    Exo. 4:14     and he said, Is not A the Levite thy       [H175]',
        '    Exo. 4:27     And the LORD said to A, Go into the        [H175]',
        'Exo. 12:43   And the LORD said unto Moses and A,            ',
        'Exo. 12:50   commanded Moses and A, so did they.            ',
        '  Mat. 22:17   it lawful to give tribute unto C, or not?     [G2541]',
        'CAESAR AUGUSTUS',
        '  See CAESAR and See AUGUSTUS.'
    ]
    
    # Test different patterns for verse extraction
    patterns = {
        'current_failing': r'([A-Za-z0-9\.]+)\s+(\d+):(\d+)\s+(.+?)(?:\s*\[([HG]\d+)\])?',
        'improved_indented': r'^\s*([A-Za-z0-9\.]+)\s+(\d+):(\d+)\s+(.+?)(?:\s*\[([HG]\d+)\])?\s*$',
        'flexible_spacing': r'^\s*([A-Za-z0-9\.]+)\s+(\d+):\s*(\d+)\s+(.+?)(?:\s*\[([HG]\d+)\])?\s*$'
    }
    
    print("=== STRONG'S NUMBER EXTRACTION TEST ===\n")
    
    for pattern_name, pattern in patterns.items():
        print(f"{pattern_name.upper()}:")
        for line in test_lines:
            match = re.match(pattern, line)
            if match:
                book = match.group(1).rstrip('.')
                chapter = match.group(2)
                verse = match.group(3)
                context = match.group(4).strip()
                strong_num = match.group(5) if len(match.groups()) >= 5 and match.group(5) else "None"
                print(f"  ✓ {book} {chapter}:{verse} [{strong_num}] - {context[:30]}...")
            else:
                print(f"  ✗ NO MATCH: {line[:50]}...")
        print()

def create_robust_parser():
    """Create and test a robust parsing function."""
    
    def parse_concordance_robust(content):
        """Robust concordance parser that handles all edge cases."""
        
        lines = content.split('\n')
        entries = []
        current_word = None
        
        # Patterns
        word_header_pattern = r'^([A-Z][A-Z\'-]*(?:\s+[A-Z][A-Z\'-]*)*)$'
        verse_pattern = r'^\s*([A-Za-z0-9\.]+)\s+(\d+):\s*(\d+)\s+(.+?)(?:\s*\[([HG]\d+)\])?\s*$'
        see_reference_pattern = r'^\s*See\s+[A-Z]'
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Skip empty lines and "See" reference lines
            if not line_stripped or re.match(see_reference_pattern, line_stripped):
                continue
            
            # Check for word header
            word_match = re.match(word_header_pattern, line_stripped)
            if word_match:
                # For compound headers like "CAESAR AUGUSTUS", take first word only
                current_word = word_match.group(1).split()[0]
                continue
            
            # Check for verse reference
            verse_match = re.match(verse_pattern, line)
            if verse_match and current_word:
                book_abbrev = verse_match.group(1).rstrip('.')
                chapter = int(verse_match.group(2))
                verse = int(verse_match.group(3))
                context = verse_match.group(4).strip()
                strong_number = verse_match.group(5) if verse_match.group(5) else None
                
                entries.append({
                    'word': current_word,
                    'book': book_abbrev,
                    'chapter': chapter,
                    'verse': verse,
                    'context': context,
                    'strong_number': strong_number,
                    'line_number': i + 1
                })
        
        return entries
    
    # Test with sample content
    test_content = """A
    See the Appendix.

AARON
    Exo. 4:14     and he said, Is not A the Levite thy       [H175]
    Exo. 4:27     And the LORD said to A, Go into the        [H175]
    Exo. 4:28     And Moses told A all the words of the      [H175]

CAESAR
  Mat. 22:17   it lawful to give tribute unto C, or not?     [G2541]
  Mat. 22:21   therefore unto C the things which are         [G2541]

CAESAR AUGUSTUS
  See CAESAR and See AUGUSTUS.

FOURTEEN
  Gen. 31:41   served thee f years for thy two               [H702]"""

    print("=== ROBUST PARSER TEST ===\n")
    entries = parse_concordance_robust(test_content)
    
    for entry in entries:
        print(f"Word: {entry['word']:10} | {entry['book']} {entry['chapter']}:{entry['verse']} | Strong's: {entry['strong_number'] or 'None':5} | Line: {entry['line_number']:3}")
    
    print(f"\nTotal entries parsed: {len(entries)}")
    
    # Check if we caught AARON and CAESAR
    words_found = {entry['word'] for entry in entries}
    print(f"Words found: {sorted(words_found)}")
    
    return parse_concordance_robust

if __name__ == "__main__":
    test_strongs_extraction()
    create_robust_parser()