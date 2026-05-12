#!/usr/bin/env python3
"""
Extract questions from 3ABN Bible Q&A VTT transcripts.
Outputs a structured list of questions grouped by episode.
"""

import os
import re
import sys

TRANSCRIPT_DIR = "/home/nigel/tinyowl/curation/transcripts/3abn-bible-qa"

def clean_vtt(path):
    """Strip VTT markup and deduplicate lines."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    # Remove WEBVTT header and metadata
    raw = re.sub(r'^WEBVTT.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^Kind:.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^Language:.*?\n', '', raw, flags=re.MULTILINE)
    # Remove timestamp lines
    raw = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d+ --> .*\n', '', raw, flags=re.MULTILINE)
    # Remove sequence numbers
    raw = re.sub(r'^\d+\s*\n', '', raw, flags=re.MULTILINE)
    # Remove inline time tags like <00:00:01.280><c> or </c>
    raw = re.sub(r'<[^>]+>', '', raw)
    # Decode HTML entities
    raw = raw.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
    # Split into lines and deduplicate consecutive identical lines
    lines = []
    prev = None
    for line in raw.split('\n'):
        line = line.strip()
        if line and line != prev:
            lines.append(line)
            prev = line
    return ' '.join(lines)

def extract_questions(text):
    """
    Extract viewer questions from 3ABN Bible Q&A transcripts.
    
    Pattern 1: text followed by attribution like "that's from [name] in [state]"
    Pattern 2: text followed by "who texted/emailed that to us"
    Pattern 3: blocks starting with question-intro phrases
    """
    questions = []
    
    # Pattern: [question text] that's from [Name] in [Location] who (texted|emailed|sent)
    # The question block usually ends just before the attribution
    attr_pattern = re.compile(
        r'([A-Z][^.!?]{20,}?[?])'  # question ending in ?
        r'(?=[^.]*?(?:that\'s from|who texted|who emailed|who sent|from [A-Z][a-z]+ (?:in|who)))',
        re.IGNORECASE
    )
    for m in attr_pattern.finditer(text):
        q = m.group(1).strip()
        if len(q) > 30:
            questions.append(q)
    
    # Pattern: look for text between "question" intro and next attribution or answer start
    # Find viewer-submitted question blocks
    block_pattern = re.compile(
        r'(?:here\'s your (?:first|next|last|second|third|final) question'  
        r'|i\'ve got your (?:first|next|last|second|third|final) question'
        r'|(?:first|next|last|second|third|final) question (?:is |comes )?from'
        r'|(?:texted|emailed|sent) (?:in |us )?(?:this question )?(?:and )?(?:(?:he|she|they) (?:asks?|wants to know))[,:]?\s*)'
        r'(.{30,}?[?])',
        re.IGNORECASE | re.DOTALL
    )
    for m in block_pattern.finditer(text):
        q = m.group(1).strip()
        # Clean up leading punctuation
        q = re.sub(r'^[,;:\s]+', '', q)
        if len(q) > 30 and q not in questions:
            questions.append(q)
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in questions:
        key = re.sub(r'\s+', ' ', q.lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(q)
    
    return unique

def get_episode_info(filename):
    """Extract episode number and title from filename."""
    basename = os.path.basename(filename)
    match = re.match(r'^(\d+)-([A-Za-z0-9_-]+)-(.+)\.en\.vtt$', basename)
    if match:
        idx = match.group(1)
        video_id = match.group(2)
        title = match.group(3).replace('｜', '|').strip()
        # Clean up title
        title = re.sub(r'\s*\|?\s*3ABN Bible Q\s*&?\s*A\.?\s*$', '', title, flags=re.IGNORECASE).strip()
        return idx, video_id, title
    return "???", "???", basename

def main():
    vtt_files = sorted([
        os.path.join(TRANSCRIPT_DIR, f)
        for f in os.listdir(TRANSCRIPT_DIR)
        if f.endswith('.en.vtt')
    ])
    
    print(f"Processing {len(vtt_files)} episodes...\n")
    
    all_questions = []
    
    for vtt_path in vtt_files:
        idx, video_id, title = get_episode_info(vtt_path)
        text = clean_vtt(vtt_path)
        questions = extract_questions(text)
        
        if questions:
            all_questions.append({
                'episode': idx,
                'video_id': video_id,
                'title': title,
                'questions': questions
            })
            print(f"## Episode {idx}: {title}")
            for q in questions:
                print(f"  - {q}")
            print()
    
    print(f"\n--- TOTAL EPISODES WITH QUESTIONS: {len(all_questions)} ---")
    total_q = sum(len(e['questions']) for e in all_questions)
    print(f"--- TOTAL QUESTIONS EXTRACTED: {total_q} ---")

if __name__ == "__main__":
    main()
