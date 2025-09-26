#!/usr/bin/env python3
"""
Ingest Spirit of Prophecy PDFs (paragraph + chapter layers).

Scopes:
  --scope coa   : Conflict of the Ages (5 books)
  --scope all   : All SOP PDFs found (Downloads SOP folder + raw dir)

Collections:
  - sop_paragraphs
  - sop_chapters

Safety:
  - Backs up existing SOP collections before re-creating
  - Idempotent: if target counts match, skip re-embed
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).resolve().parents[1]
VDB_PATH = str(ROOT / "vectordb")
BACKUP_DIR = str(ROOT / "backups")

# Optional safety backup
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
try:
    from safety import backup_collection as _backup_collection  # type: ignore
except Exception:
    _backup_collection = None


# Preferred sources
RAW_DIR = ROOT / "domains/theology/raw"
DL_SOP_DIR = Path.home() / "Downloads/Spirit Of Prophecy (1)-20250925T083805Z-1-001/Spirit Of Prophecy (1)"

# COA canonical filenames in RAW_DIR
COA_FILES = [
    "PatriarchsAndProphets.pdf",
    "ProphetsAndKings.pdf",
    "DesireofAges.pdf",
    "ActsofTheApostles.pdf",
    "The Great Controversy.pdf",
]


# Simple PDF text extraction with fallback
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None  # type: ignore


FRONT_MATTER_PATTERNS = (
    re.compile(r"Ellen G\. White Estate", re.I),
    re.compile(r"Information about this Book", re.I),
    re.compile(r"Overview", re.I),
    re.compile(r"This ePub publication is provided", re.I),
)


def pdf_to_text(path: Path, max_pages: int | None = None) -> str:
    raw = ""
    if PdfReader is not None:
        try:
            rd = PdfReader(str(path))
            pages = rd.pages if max_pages is None else rd.pages[:max_pages]
            parts: List[str] = []
            for pg in pages:
                t = (pg.extract_text() or "").replace("\r\n", "\n").replace("\r", "\n")
                parts.append(t)
            raw = "\n".join(parts)
        except Exception:
            raw = ""
    if not raw.strip():
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=True) as tmp:
            cmd = ["pdftotext", "-layout", str(path), tmp.name]
            if max_pages:
                cmd = ["pdftotext", "-layout", "-l", str(max_pages), str(path), tmp.name]
            try:
                subprocess.run(cmd, check=True)
                raw = Path(tmp.name).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                raw = ""
    return raw.replace("\r\n", "\n").replace("\r", "\n")


def paragraphize(raw: str) -> List[str]:
    paras = [p.strip() for p in raw.split("\n\n")]
    out: List[str] = []
    for p in paras:
        if len(p) < 100:
            continue
        if any(rx.search(p) for rx in FRONT_MATTER_PATTERNS):
            continue
        out.append(p)
    if out:
        return out
    # Fallback: build paragraphs from lines
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    buf: List[str] = []
    out = []
    def flush():
        if not buf:
            return
        para = " ".join(buf).strip()
        if len(para) >= 120 and not any(rx.search(para) for rx in FRONT_MATTER_PATTERNS):
            out.append(para)
        buf.clear()
    for ln in lines:
        buf.append(ln)
        if len(" ".join(buf)) >= 600 or ln.endswith(('.', '?', '!')):
            flush()
    flush()
    return out


def chapterize(raw: str) -> List[str]:
    # Try to split by CHAPTER headings; fallback to size-based chunks
    blocks: List[str] = []
    # Normalize
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    cur: List[str] = []
    chapter_header = re.compile(r"^(?:CHAPTER|Chapter)\s+\d+", re.I)
    for ln in lines:
        if chapter_header.match(ln.strip()) and cur:
            blocks.append("\n".join(cur).strip())
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip())
    # Filter small/front matter blocks
    blocks = [b for b in blocks if len(b) >= 800 and not any(rx.search(b) for rx in FRONT_MATTER_PATTERNS)]
    if blocks:
        return blocks
    # Fallback: chunk by length
    paras = paragraphize(raw)
    chunks: List[str] = []
    buf: List[str] = []
    for p in paras:
        if sum(len(x) for x in buf) >= 3000:
            chunks.append("\n\n".join(buf))
            buf = []
        buf.append(p)
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


@dataclass
class Doc:
    book: str
    fmt: str
    text: str


def load_scope(scope: str) -> List[Path]:
    files: List[Path] = []
    if scope == "coa":
        for name in COA_FILES:
            p = RAW_DIR / name
            if p.exists():
                files.append(p)
    else:
        seen: set[str] = set()
        # Put COA first in a consistent order
        for name in COA_FILES:
            p = RAW_DIR / name
            if p.exists():
                files.append(p)
                seen.add(p.name.lower())
        # then from raw dir (excluding COA)
        for p in sorted(RAW_DIR.glob("*.pdf")):
            key = p.name.lower()
            if key in seen:
                continue
            seen.add(key)
            files.append(p)
        # from downloads SOP dir
        if DL_SOP_DIR.exists():
            for p in sorted(DL_SOP_DIR.glob("*.pdf")):
                key = p.name.lower()
                if key in seen:
                    continue
                seen.add(key)
                files.append(p)
    return files


def recreate(client: chromadb.ClientAPI, name: str, ef) -> chromadb.Collection:
    try:
        existing = client.get_collection(name)
        count = 0
        try:
            count = existing.count()
        except Exception:
            count = 0
        if _backup_collection is not None and count:
            try:
                backup_path = _backup_collection(VDB_PATH, name, BACKUP_DIR)
                print(f"  🔒 Backup created: {backup_path}")
            except Exception as e:
                print(f"  ⚠️ Backup failed ({e}); proceeding")
        client.delete_collection(name)
    except Exception:
        pass
    return client.create_collection(name=name, embedding_function=ef, metadata={"description": name})


def add_docs(col, docs: List[str], metas: List[Dict], batch: int = 96, start_index: int = 0) -> int:
    total = len(docs)
    for i in range(0, total, batch):
        j = min(i + batch, total)
        ids = [f"{col.name}_{start_index + k}" for k in range(i, j)]
        col.add(ids=ids, documents=docs[i:j], metadatas=metas[i:j])
        if ((i // batch) + 1) % 10 == 0 or j == total:
            print(f"    Batch {(i//batch)+1}/{(total+batch-1)//batch} complete")
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest SOP PDFs into paragraph/chapter collections")
    ap.add_argument("--scope", choices=["coa", "all"], default="coa")
    ap.add_argument("--recreate", action="store_true", help="Backup + recreate SOP collections before embedding")
    ap.add_argument("--batch", type=int, default=int(__import__('os').environ.get('TINYOWL_SOP_BATCH', '96')), help="Embedding batch size (default from env TINYOWL_SOP_BATCH or 96)")
    args = ap.parse_args()

    files = load_scope(args.scope)
    if not files:
        raise SystemExit("No SOP PDFs found for the selected scope")
    print(f"🦉 SOP ingest scope: {args.scope} — {len(files)} files")

    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='BAAI/bge-large-en-v1.5')
    client = chromadb.PersistentClient(path=VDB_PATH)

    print("\n🗃️  Preparing collections…")
    if args.recreate:
        print("  ♻️  Recreate mode enabled")
        col_par = recreate(client, "sop_paragraphs", bge_ef)
        col_chp = recreate(client, "sop_chapters", bge_ef)
        par_existing = 0
        chp_existing = 0
    else:
        # Resume-aware get/create
        def get_or_create_resume(name: str):
            try:
                col = client.get_collection(name)
                try:
                    existing = col.count()
                except Exception:
                    existing = 0
                print(f"  ⚠️ {name} exists with {existing} items (resume)")
                return col, existing
            except Exception:
                pass
            # create new
            col = client.create_collection(name=name, embedding_function=bge_ef, metadata={"description": name})
            print(f"  ✅ Created {name}")
            return col, 0

        col_par, par_existing = get_or_create_resume("sop_paragraphs")
        col_chp, chp_existing = get_or_create_resume("sop_chapters")

    all_par_docs: List[str] = []
    all_par_meta: List[Dict] = []
    all_chp_docs: List[str] = []
    all_chp_meta: List[Dict] = []

    for idx, path in enumerate(files, 1):
        try:
            print(f"\n📖 [{idx}/{len(files)}] {path.name}")
            raw = pdf_to_text(path)
            if not raw.strip():
                print("  ⚠️ Empty extraction; skipping")
                continue
            paras = paragraphize(raw)
            chaps = chapterize(raw)
            book = path.stem
            # Build metadata
            for i, p in enumerate(paras):
                all_par_docs.append(p)
                all_par_meta.append({
                    "source": "spirit_of_prophecy",
                    "book": book,
                    "authority_level": "spirit_of_prophecy",
                    "unit": "paragraph",
                    "index": i,
                    "file": path.name,
                })
            for i, c in enumerate(chaps):
                all_chp_docs.append(c)
                all_chp_meta.append({
                    "source": "spirit_of_prophecy",
                    "book": book,
                    "authority_level": "spirit_of_prophecy",
                    "unit": "chapter",
                    "index": i,
                    "file": path.name,
                })
            print(f"  ➕ paragraphs: {len(paras)} | chapters: {len(chaps)}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue

    # Persist chunk JSONs for transparency
    chunks_dir = ROOT / "domains/theology/chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    (chunks_dir / "sop_paragraphs.json").write_text(
        __import__('json').dumps(all_par_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (chunks_dir / "sop_chapters.json").write_text(
        __import__('json').dumps(all_chp_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n💾 Saved chunk lists: sop_paragraphs.json ({len(all_par_docs)}), sop_chapters.json ({len(all_chp_docs)})")

    print("\n⚙️  Embedding paragraphs…")
    if par_existing < len(all_par_docs):
        # resume from par_existing
        add_docs(col_par, all_par_docs[par_existing:], all_par_meta[par_existing:], batch=args.batch, start_index=par_existing)
    else:
        print("  ✅ Up-to-date")
    print("⚙️  Embedding chapters…")
    if chp_existing < len(all_chp_docs):
        add_docs(col_chp, all_chp_docs[chp_existing:], all_chp_meta[chp_existing:], batch=args.batch, start_index=chp_existing)
    else:
        print("  ✅ Up-to-date")

    print("\n📊 Final counts:")
    print(f"  sop_paragraphs: {col_par.count()}")
    print(f"  sop_chapters  : {col_chp.count()}")
    print("\n✅ SOP ingest complete.")


if __name__ == "__main__":
    main()
