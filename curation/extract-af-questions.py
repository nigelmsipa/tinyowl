#!/usr/bin/env python3
"""
Extract caller questions from Amazing Facts Bible Answers Live VTT transcripts.
Callers phone in live; questions are in the caller's own voice, not read by a host.
"""

import os
import re
import sys

TRANSCRIPT_DIR = "/home/nigel/tinyowl/curation/transcripts/amazing-facts-qa"
OUTPUT_FILE = "/home/nigel/tinyowl/curation/af-questions-raw.txt"

def clean_vtt(path):
    """Strip VTT markup and deduplicate lines."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r'^WEBVTT.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^Kind:.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^Language:.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d+ --> .*\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^\d+\s*\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = raw.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
    lines = []
    prev = None
    for line in raw.split('\n'):
        line = line.strip()
        if line and line != prev:
            lines.append(line)
            prev = line
    return ' '.join(lines)


# Patterns that signal the host is responding (caller segment ends)
HOST_RESPONSE_PATTERNS = re.compile(
    r'\b(?:'
    r'great question|good question|that\'s a great|that\'s a good|that\'s an? (interesting|important|great|good)'
    r'|yeah[,\s]+(?:well|I|that|so|uh)|well[,\s]+(?:I|that|so|uh|first)'
    r'|let me (?:share|explain|tell|read|give|take|answer)'
    r'|I do think|I think what|here\'s what I think|here\'s the thing'
    r'|Pastor (?:Doug|Ross|Bachelor)[,\s]'
    r'|so (?:first|the|what|here)'
    r'|the answer (?:is|to that)'
    r'|you know[,\s]+(?:the|that|I|in|Paul|Jesus|God)'
    r')\b',
    re.IGNORECASE
)

# Caller introduction pattern — always "[Name] welcome to the program/Bible answers live/the air"
CALLER_INTRO = re.compile(
    r'[A-Za-z]+ welcome to (?:the program|Bible (?:answers live|answers)|the air)\b',
    re.IGNORECASE
)

# Phrases that signal the explicit question being stated
QUESTION_INTRO = re.compile(
    r'(?:my question is|i have a question|i\'ve got a question|i\'d like to ask|'
    r'my question (?:is |has )?(?:to do )?(?:with |about |is )?|'
    r'i was wondering|i want to know|can you (?:explain|tell me|help me)|'
    r'what (?:does|is|are|do)|how (?:can|do|does|is|are)|'
    r'is (?:it|there|this|that)|why (?:is|are|does|did|would|can))',
    re.IGNORECASE
)


def extract_caller_questions(text):
    """
    Find each caller segment and extract question content.
    Auto-captions don't reliably punctuate questions with ?, so we extract
    by phrase boundary: from the question-intro phrase to the host-response signal.
    """
    questions = []

    intro_matches = list(CALLER_INTRO.finditer(text))

    # Skip the very first match if it's the show intro ("God welcome to Bible answers live")
    start_idx = 0
    if intro_matches and re.search(r'\bGod\b', text[max(0, intro_matches[0].start()-10):intro_matches[0].start()], re.IGNORECASE):
        start_idx = 1

    for i, intro_match in enumerate(intro_matches[start_idx:], start=start_idx):
        start = intro_match.end()
        # End of this caller's segment = start of next caller intro (or +1500 chars)
        if i + 1 < len(intro_matches):
            end = min(start + 1500, intro_matches[i + 1].start())
        else:
            end = start + 1500
        segment = text[start:end]

        # Find the question-intro phrase
        qi = QUESTION_INTRO.search(segment)
        if not qi:
            continue

        # Extract from the question-intro phrase onward
        q_text = segment[qi.start():]

        # Truncate at the first host-response signal
        resp = HOST_RESPONSE_PATTERNS.search(q_text)
        if resp:
            q_text = q_text[:resp.start()]

        # Trim to a reasonable question length (not the entire call monologue)
        q_text = q_text.strip()
        if len(q_text) > 350:
            # Try to cut at a sentence break within 350 chars
            trunc = q_text[:350]
            last_period = max(trunc.rfind('. '), trunc.rfind('? '), trunc.rfind('! '))
            if last_period > 80:
                q_text = trunc[:last_period + 1]
            else:
                q_text = trunc

        # Remove the question-intro prefix itself to get the bare question
        # e.g. "my question is are they the angels" -> "Are they the angels?"
        q_clean = re.sub(
            r'^(?:my question is|i have a question[\w\s,]*about|i\'ve got a question[\w\s]*|'
            r'my question (?:has )?to do with|i was wondering|i want to know)[,:]?\s*',
            '', q_text, flags=re.IGNORECASE
        ).strip()

        if not q_clean:
            q_clean = q_text.strip()

        # Capitalise and add ? if needed
        if q_clean:
            q_clean = q_clean[0].upper() + q_clean[1:]
            if not q_clean.endswith('?'):
                q_clean += '?'

        if len(q_clean) > 30:
            questions.append(q_clean)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for q in questions:
        key = re.sub(r'\s+', ' ', q.lower().strip())[:100]
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
        title = re.sub(r'\s*\(Bible Answers Live\).*$', '', title, flags=re.IGNORECASE).strip()
        return idx, video_id, title
    return "???", "???", basename


def main():
    vtt_files = sorted([
        os.path.join(TRANSCRIPT_DIR, f)
        for f in os.listdir(TRANSCRIPT_DIR)
        if f.endswith('.en.vtt')
    ])

    print(f"Processing {len(vtt_files)} episodes...\n")

    all_episodes = []

    for vtt_path in vtt_files:
        idx, video_id, title = get_episode_info(vtt_path)
        text = clean_vtt(vtt_path)
        questions = extract_caller_questions(text)

        if questions:
            all_episodes.append({
                'episode': idx,
                'video_id': video_id,
                'title': title,
                'questions': questions
            })
            print(f"## Episode {idx}: {title}")
            for q in questions:
                print(f"  - {q}")
            print()

    total_q = sum(len(e['questions']) for e in all_episodes)
    print(f"\n--- TOTAL EPISODES WITH QUESTIONS: {len(all_episodes)} ---")
    print(f"--- TOTAL QUESTIONS EXTRACTED: {total_q} ---")

    # Write output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("# Amazing Facts — Bible Answers Live: Extracted Caller Questions\n\n")
        for ep in all_episodes:
            out.write(f"## Episode {ep['episode']}: {ep['title']}\n")
            out.write(f"<!-- video_id: {ep['video_id']} -->\n\n")
            for q in ep['questions']:
                out.write(f"- {q}\n")
            out.write("\n")
        out.write(f"\n---\nTotal questions: {total_q}\n")

    print(f"\nOutput written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
