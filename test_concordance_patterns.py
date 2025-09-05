#!/usr/bin/env python3
"""
Test script to analyze Strong's Concordance parsing patterns
"""
import re
from pathlib import Path

def analyze_concordance_patterns():
    """Analyze different patterns in the concordance file."""
    
    concordance_file = Path("domains/theology/raw/strongs_concordance_complete.txt")
    
    with open(concordance_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find start of concordance entries (skip introduction)
    concordance_start = content.find("AARON")
    concordance_content = content[concordance_start:concordance_start + 50000]  # First 50k chars for analysis
    
    lines = concordance_content.split('\n')
    
    # Pattern categories
    patterns = {
        'standalone_word': r'^([A-Z][A-Z\'-]*)$',                         # AARON, CAESAR
        'compound_word': r'^([A-Z][A-Z\'-]*\s+[A-Z][A-Z\'-]*)$',         # CAESAR AUGUSTUS
        'word_with_content': r'^([A-Z][A-Z\'-]+)\s+(.+)',                # Current failing pattern
        'indented_verse': r'^\s+([A-Za-z0-9\.]+)\s+(\d+):(\d+)\s+(.+)',  # Verse references
        'blank_line': r'^\s*$'
    }
    
    results = {name: [] for name in patterns}
    line_types = []
    
    for i, line in enumerate(lines[:200]):  # Analyze first 200 lines
        line_type = 'unknown'
        
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, line):
                results[pattern_name].append((i, line))
                line_type = pattern_name
                break
        
        line_types.append((i, line, line_type))
    
    # Print analysis
    print("=== CONCORDANCE PATTERN ANALYSIS ===\n")
    
    for pattern_name, matches in results.items():
        print(f"{pattern_name.upper()}: {len(matches)} matches")
        for i, line in matches[:5]:  # Show first 5 examples
            print(f"  Line {i}: '{line}'")
        if len(matches) > 5:
            print(f"  ... and {len(matches) - 5} more")
        print()
    
    # Show sequence of line types
    print("=== LINE SEQUENCE ANALYSIS ===")
    for i, line, line_type in line_types[:50]:
        print(f"{i:3d}: {line_type:15} | {repr(line[:60])}")
    
    # Test improved parsing logic
    print("\n=== TESTING IMPROVED PARSING LOGIC ===")
    test_improved_parser(lines[:50])

def test_improved_parser(lines):
    """Test an improved parsing approach."""
    
    current_word = None
    entries_found = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a word header (standalone or compound)
        if re.match(r'^[A-Z][A-Z\'-]*(?:\s+[A-Z][A-Z\'-]*)*$', line):
            # Split compound words - take only the first word
            current_word = line.split()[0]
            print(f"Found word header: '{current_word}' from line '{line}'")
            continue
        
        # Check if this is a verse reference line
        verse_match = re.match(r'([A-Za-z0-9\.]+)\s+(\d+):(\d+)\s+(.+?)(?:\s*\[([HG]\d+)\])?', line)
        if verse_match and current_word:
            book_abbrev = verse_match.group(1).rstrip('.')
            chapter = verse_match.group(2)
            verse = verse_match.group(3)
            context = verse_match.group(4).strip()
            strong_number = verse_match.group(5) if verse_match.group(5) else None
            
            print(f"  Entry: {current_word} -> {book_abbrev} {chapter}:{verse} [{strong_number or 'No Strong#'}]")
            entries_found += 1
    
    print(f"\nImproved parser found {entries_found} entries in first 50 lines")

if __name__ == "__main__":
    analyze_concordance_patterns()