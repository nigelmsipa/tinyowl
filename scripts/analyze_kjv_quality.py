#!/usr/bin/env python3
"""
Analyze KJV text quality for TinyOwl ingestion
"""

import re
from collections import defaultdict
from text_normalizer import TextNormalizer
from canonical_validator import CanonicalValidator

def analyze_kjv_quality(filepath):
    """Analyze KJV text file quality"""
    print("=" * 60)
    print("KJV TEXT QUALITY ANALYSIS")
    print("=" * 60)
    
    # Read file with correct encoding
    try:
        with open(filepath, 'r', encoding='latin1') as f:
            lines = f.readlines()
        print(f"✅ File readable: {len(lines):,} lines")
    except Exception as e:
        print(f"❌ File read error: {e}")
        return
    
    # Basic statistics
    print(f"📊 File size: {len(''.join(lines)):,} characters")
    
    # Check structure
    chapter_pattern = re.compile(r'^CHAPTER\s+\d+', re.IGNORECASE)
    book_pattern = re.compile(r'^[A-Z\s]+$')
    verse_pattern = re.compile(r'^\s*\d+\s+')
    
    chapters = []
    books = []
    verses = []
    
    current_book = None
    current_chapter = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for book names (all caps lines)
        if book_pattern.match(line) and len(line) > 3 and len(line) < 50:
            # Skip obvious headers
            if not any(word in line.lower() for word in ['holy', 'bible', 'testament', 'king', 'james']):
                if line not in ['TO THE READER', 'THE TRANSLATORS TO THE READER']:
                    books.append(line)
                    current_book = line
                    print(f"📖 Found book: {line}")
        
        # Check for chapters
        elif chapter_pattern.match(line):
            chapter_num = re.search(r'\d+', line).group()
            chapters.append((current_book, int(chapter_num)))
            current_chapter = int(chapter_num)
            
        # Check for verses
        elif verse_pattern.match(line):
            verse_match = re.match(r'^\s*(\d+)\s+(.+)', line)
            if verse_match:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2)
                verses.append((current_book, current_chapter, verse_num, verse_text))
    
    print(f"\n📚 Structure Analysis:")
    print(f"   Books found: {len(books)}")
    print(f"   Chapters found: {len(chapters)}")
    print(f"   Verses found: {len(verses):,}")
    
    # Show first few books
    print(f"\n📖 First 10 books:")
    for book in books[:10]:
        print(f"   - {book}")
    
    # Verse distribution by book
    verse_by_book = defaultdict(int)
    for book, chapter, verse_num, text in verses:
        if book:
            verse_by_book[book] += 1
    
    print(f"\n📊 Verses per book (top 10):")
    sorted_books = sorted(verse_by_book.items(), key=lambda x: x[1], reverse=True)
    for book, count in sorted_books[:10]:
        print(f"   {book}: {count:,} verses")
    
    # Check for common Bible books
    expected_books = ['GENESIS', 'EXODUS', 'MATTHEW', 'JOHN', 'REVELATION']
    found_expected = [book for book in expected_books if any(book in found.upper() for found in books)]
    print(f"\n✅ Expected books found: {found_expected}")
    
    # Sample verses quality
    print(f"\n📝 Sample verse quality:")
    sample_verses = verses[100:105]  # Sample from Genesis
    for book, chapter, verse_num, text in sample_verses:
        print(f"   {book} {chapter}:{verse_num} - {text[:80]}{'...' if len(text) > 80 else ''}")
    
    # Character encoding issues
    print(f"\n🔍 Encoding quality check:")
    problematic_chars = []
    for i, line in enumerate(lines[:1000]):  # Check first 1000 lines
        for char in line:
            if ord(char) > 127:  # Non-ASCII characters
                if char not in problematic_chars:
                    problematic_chars.append(char)
    
    if problematic_chars:
        print(f"   ⚠️  Non-ASCII characters found: {problematic_chars[:10]}")
        print(f"   Total unique non-ASCII: {len(problematic_chars)}")
    else:
        print(f"   ✅ Clean ASCII text")
    
    # Estimate coverage
    expected_verses = 31102  # Canonical total
    coverage_percent = (len(verses) / expected_verses) * 100
    print(f"\n📈 Coverage estimate: {coverage_percent:.1f}% ({len(verses):,}/{expected_verses:,} verses)")
    
    # Quality rating
    print(f"\n⭐ QUALITY ASSESSMENT:")
    
    quality_score = 0
    max_score = 5
    
    # Readability (1 point)
    if len(lines) > 30000:
        quality_score += 1
        print(f"   ✅ File size appropriate: +1")
    
    # Structure (1 point)
    if len(books) >= 60 and len(chapters) >= 1000:
        quality_score += 1
        print(f"   ✅ Good structure detected: +1")
    
    # Verse count (1 point)
    if len(verses) > 25000:  # At least 80% coverage
        quality_score += 1
        print(f"   ✅ Good verse coverage: +1")
    
    # Expected books (1 point)
    if len(found_expected) >= 4:
        quality_score += 1
        print(f"   ✅ Key books present: +1")
    
    # Clean encoding (1 point)
    if len(problematic_chars) < 10:
        quality_score += 1
        print(f"   ✅ Clean encoding: +1")
    
    print(f"\n🏆 OVERALL QUALITY: {quality_score}/{max_score}")
    
    if quality_score >= 4:
        print(f"✅ EXCELLENT - Ready for bulletproof ingestion!")
    elif quality_score >= 3:
        print(f"✅ GOOD - Minor cleanup may be needed")
    elif quality_score >= 2:
        print(f"⚠️  FAIR - Significant preprocessing required")
    else:
        print(f"❌ POOR - Find better source text")
    
    print(f"\n💡 RECOMMENDATION:")
    if quality_score >= 4:
        print(f"   Proceed with hierarchical chunking ingestion")
        print(f"   Use latin1 encoding for file reading")
        print(f"   Apply normalization pipeline for cleanup")
    else:
        print(f"   Consider finding higher quality KJV source")
        print(f"   May need manual preprocessing")

if __name__ == "__main__":
    analyze_kjv_quality("/home/nigel/Downloads/TheHolyBibleKJV.txt")