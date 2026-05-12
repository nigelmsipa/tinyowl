#!/usr/bin/env python3
"""
Extract questions from Randy Skeete transcripts.

Two sources:
  1. randy-skeete-sessions/ — question is embedded in the video title (ALL CAPS + ？)
  2. randy-skeet-qa/        — questions are read aloud; extract via "next question" pattern
"""
import os
import re

SESSIONS_DIR = "/home/nigel/tinyowl/curation/transcripts/randy-skeete-sessions"
QA_DIR       = "/home/nigel/tinyowl/curation/transcripts/randy-skeet-qa"
OUTPUT_FILE  = "/home/nigel/tinyowl/curation/rs-questions-raw.txt"

FULLWIDTH_Q = '\uff1f'   # ？

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_vtt(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        raw = f.read()
    raw = re.sub(r'^WEBVTT.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^(?:Kind|Language):.*?\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d+ --> .*\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^\d+\s*\n', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'<[^>]+>', '', raw)
    lines = []
    prev = None
    for line in raw.split('\n'):
        line = line.strip()
        if line and line != prev:
            lines.append(line)
            prev = line
    return ' '.join(lines)


def title_from_filename(fname):
    """Strip leading NNN-VIDEOID- and .en.vtt suffix."""
    title = re.sub(r'^\d+-[A-Za-z0-9_-]+-', '', fname)
    return title.replace('.en.vtt', '').strip()


def extract_question_from_title(raw_title):
    """Pull the question out of a sessions-folder title."""
    t = raw_title
    # Remove common prefix
    t = re.sub(
        r'^Randy\s+[Ss]keete\s+[Ss]ermon\s*(?:\d{4})?\s*[-–:]*\s*',
        '', t, flags=re.IGNORECASE
    ).strip()
    t = re.sub(r'^Randy\s+[Ss]keete\s*[-–:]*\s*', '', t, flags=re.IGNORECASE).strip()
    # Remove trailing (Q&A …) / | … noise
    t = re.sub(r'\(?\s*(?:Q&A|Question and Answer)\s*(?:Session|SESSION)?\s*\)?', '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'\u2502.*$', '', t).strip()   # ｜ and everything after
    t = re.sub(r'\s+', ' ', t).strip()

    # Must contain a question mark (fullwidth or ASCII)
    if FULLWIDTH_Q not in t and '?' not in t:
        return None

    # Normalise fullwidth ? → ?
    t = t.replace(FULLWIDTH_Q, '?')
    # Extract up to and including the first ?
    m = re.search(r'^(.+?\?)', t)
    if m:
        t = m.group(1).strip()
    # Title-case and tidy whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) < 15:
        return None
    return t


# ---------------------------------------------------------------------------
# Source 1 — sessions filenames
# ---------------------------------------------------------------------------

def extract_from_sessions():
    questions = []
    files = sorted(f for f in os.listdir(SESSIONS_DIR) if f.endswith('.vtt'))
    for fname in files:
        raw_title = title_from_filename(fname)
        q = extract_question_from_title(raw_title)
        if q:
            # Capitalise first letter
            q = q[0].upper() + q[1:]
            questions.append(('sessions', fname, q))
    return questions


# ---------------------------------------------------------------------------
# Source 2 — QA transcripts: "next question [text]" pattern
# ---------------------------------------------------------------------------

NEXT_Q_RE = re.compile(
    r'(?:'
    r'(?:okay\s+)?(?:the\s+)?next\s+question\s+(?:is\s+)?'
    r'|the\s+question\s+is\s+'
    r'|question\s+(?:number\s+)?\d+\s+(?:is\s+)?'
    r'|question\s+(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:is\s+)?'
    r'|(?:okay\s+)?(?:alright\s+)?(?:so\s+)?(?:the\s+)?(?:next\s+)?question\s+reads?\s+(?:like\s+this\s+)?'
    r')',
    re.IGNORECASE
)

# Signal that the answer has started (don't include this in the question)
ANSWER_START_RE = re.compile(
    r'\b(?:let\s+(?:me|us)\s+(?:pray|read|look)|'
    r'father\s+in\s+heaven|in\s+(?:the\s+)?bible|'
    r'the\s+bible\s+says|read(?:ing)?\s+from|in\s+genesis|in\s+revelation|'
    r'in\s+(?:first|second|third)?\s*(?:john|peter|paul|acts|matthew|luke|mark|romans|hebrews|james|corinthians)\b)',
    re.IGNORECASE
)


def extract_from_qa():
    questions = []
    files = sorted(f for f in os.listdir(QA_DIR) if f.endswith('.vtt'))
    for fname in files:
        path = os.path.join(QA_DIR, fname)
        text = clean_vtt(path)

        for m in NEXT_Q_RE.finditer(text):
            seg_start = m.end()
            seg_end   = min(seg_start + 400, len(text))
            segment   = text[seg_start:seg_end]

            # Stop at the next question intro or answer start
            next_q = NEXT_Q_RE.search(segment)
            ans    = ANSWER_START_RE.search(segment)

            cut = len(segment)
            if next_q:
                cut = min(cut, next_q.start())
            if ans:
                cut = min(cut, ans.start())

            q = segment[:cut].strip()

            # Clean up: remove filler / trailing non-question fragments
            q = re.sub(r'\s+', ' ', q).strip()
            q = re.sub(r'^(?:okay|alright|yes|uh|uh-huh|mhm)[,.]?\s*', '', q, flags=re.IGNORECASE).strip()

            # Must be a real question
            if len(q) < 25:
                continue
            if not re.search(r'\b(?:what|how|why|when|where|who|which|is|are|do|does|did|can|could|should|would|will)\b', q, re.IGNORECASE):
                continue

            # Capitalise and ensure ends with ?
            q = q[0].upper() + q[1:]
            if not q.endswith('?'):
                q = re.sub(r'[.!]*$', '', q) + '?'

            if len(q) > 400:
                # Trim at last sentence break
                trunc = q[:400]
                last = max(trunc.rfind('? '), trunc.rfind('. '))
                q = trunc[:last + 1] if last > 60 else trunc

            questions.append(('qa', fname, q))

    # Deduplicate
    seen = set()
    unique = []
    for src, fname, q in questions:
        key = re.sub(r'\s+', ' ', q.lower().strip())[:120]
        if key not in seen:
            seen.add(key)
            unique.append((src, fname, q))
    return unique


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    sessions_qs = extract_from_sessions()
    qa_qs       = extract_from_qa()

    all_qs = sessions_qs + qa_qs
    print(f"Sessions titles : {len(sessions_qs)}")
    print(f"QA transcripts  : {len(qa_qs)}")
    print(f"Total           : {len(all_qs)}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Randy Skeete — Extracted Questions\n")
        f.write(f"# Sessions (title-based): {len(sessions_qs)}\n")
        f.write(f"# QA (transcript-based): {len(qa_qs)}\n\n")

        f.write("## From Sessions Titles\n\n")
        for i, (src, fname, q) in enumerate(sessions_qs, 1):
            f.write(f"rs-{i:03d} {q}\n")
            f.write(f"        [source: {fname[:80]}]\n")

        f.write(f"\n## From QA Transcripts\n\n")
        offset = len(sessions_qs)
        for i, (src, fname, q) in enumerate(qa_qs, 1):
            f.write(f"rs-{offset+i:03d} {q}\n")
            f.write(f"        [source: {fname[:80]}]\n")

    print(f"\nWritten to {OUTPUT_FILE}")
