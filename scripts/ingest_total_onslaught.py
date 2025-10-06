#!/usr/bin/env python3
"""
Ingest Walter Veith "Total Onslaught" lecture transcripts (HTML/MD) into TinyOwl's ChromaDB.

Goals
- Handle duplicates: prefer the higher-quality version per lecture (HTML vs MD) by comparing clean text length; tie-break to HTML.
- Two layers:
  - onslaught_lectures: one document per lecture (coarse layer)
  - onslaught_paragraphs: paragraphized content across lectures (fine layer)
- Uses BGE-large embeddings for consistency with the rest of the theology DB.

Inputs
- Default source directory: ~/Downloads/Total_Onslaught_Staging (unzipped from your NoteBook_Total Onslaught zip files)
  Files look like: Source_2xx_..._total_onslaught_... .txt.html or .txt.md

Outputs
- Chroma collections: onslaught_lectures, onslaught_paragraphs
- Chunk manifests: domains/theology/chunks/total_onslaught_lectures.json, total_onslaught_paragraphs.json
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import sys

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

DEFAULT_SRC = Path.home() / "Downloads" / "Total_Onslaught_Staging"


def clean_html(text: str) -> str:
    # Remove tags and collapse whitespace; simple heuristic
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def read_file(p: Path) -> str:
    try:
        raw = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = p.read_text(errors="ignore")
    if p.suffix.lower() == ".html":
        return clean_html(raw)
    return raw.replace("\r", "\n").strip()


@dataclass
class LectureDoc:
    key: str               # grouping key without extension
    file: Path             # chosen file path
    title: str             # inferred title
    text: str              # cleaned text


def pick_best_versions(files: List[Path]) -> List[LectureDoc]:
    # Group by base without extension
    groups: Dict[str, List[Path]] = {}
    for p in files:
        key = re.sub(r"\.(html|md)$", "", p.name, flags=re.I)
        groups.setdefault(key, []).append(p)

    chosen: List[LectureDoc] = []
    for key, paths in groups.items():
        best_path: Path | None = None
        best_len = -1
        best_text = ""
        # Evaluate each candidate
        for p in paths:
            txt = read_file(p)
            score = len(txt)
            # Prefer HTML on tie (more structure typically)
            if score > best_len or (score == best_len and p.suffix.lower() == ".html"):
                best_len = score
                best_path = p
                best_text = txt
        if not best_path or best_len < 200:  # skip tiny/empty docs
            continue
        # Title inference: use first non-empty line up to 120 chars
        title = next((ln.strip() for ln in best_text.splitlines() if ln.strip()), key)[:120]
        chosen.append(LectureDoc(key=key, file=best_path, title=title, text=best_text))
    return chosen


def paragraphize(text: str) -> List[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    out: List[str] = []
    for b in blocks:
        if len(b) >= 120:
            out.append(b)
    if out:
        return out
    # Fallback: merge lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    buf: List[str] = []
    res: List[str] = []
    def flush():
        if not buf:
            return
        para = " ".join(buf).strip()
        if len(para) >= 120:
            res.append(para)
        buf.clear()
    for ln in lines:
        buf.append(ln)
        if len(" ".join(buf)) >= 600 or ln.endswith((".", "!", "?")):
            flush()
    flush()
    return res


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
    ap = argparse.ArgumentParser(description="Ingest Total Onslaught transcripts into paragraph/lecture collections")
    ap.add_argument("--src", type=str, default=str(DEFAULT_SRC), help="Path to staging directory with HTML/MD files")
    ap.add_argument("--recreate", action="store_true", help="Backup + recreate collections before embedding")
    ap.add_argument("--batch", type=int, default=96, help="Embedding batch size")
    args = ap.parse_args()

    src_dir = Path(args.src)
    if not src_dir.exists():
        raise SystemExit(f"Source directory not found: {src_dir}")

    candidates = sorted([p for p in src_dir.glob("*.*") if p.suffix.lower() in (".html", ".md")])
    if not candidates:
        raise SystemExit("No HTML/MD transcripts found in source directory")

    print(f"🦉 Total Onslaught ingest: {len(candidates)} candidate files from {src_dir}")
    chosen = pick_best_versions(candidates)
    print(f"  ✅ Selected {len(chosen)} best-version lectures (deduplicated)")

    # Build layers
    lecture_docs: List[str] = []
    lecture_meta: List[Dict] = []
    para_docs: List[str] = []
    para_meta: List[Dict] = []

    for idx, lec in enumerate(chosen, 1):
        lecture_docs.append(lec.text)
        lecture_meta.append({
            "source": "total_onslaught",
            "unit": "lecture",
            "title": lec.title,
            "file": lec.file.name,
            "index": idx,
        })
        paras = paragraphize(lec.text)
        for pi, ptxt in enumerate(paras):
            para_docs.append(ptxt)
            para_meta.append({
                "source": "total_onslaught",
                "unit": "paragraph",
                "lecture_title": lec.title,
                "lecture_file": lec.file.name,
                "paragraph_index": pi,
            })

    # Save chunk manifests
    chunks_dir = ROOT / "domains/theology/chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    (chunks_dir / "total_onslaught_lectures.json").write_text(
        __import__('json').dumps(lecture_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (chunks_dir / "total_onslaught_paragraphs.json").write_text(
        __import__('json').dumps(para_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n💾 Saved chunk lists: lectures={len(lecture_docs)}, paragraphs={len(para_docs)}")

    # Embed
    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='BAAI/bge-large-en-v1.5')
    client = chromadb.PersistentClient(path=VDB_PATH)

    print("\n🗃️  Preparing collections…")
    if args.recreate:
        print("  ♻️  Recreate mode enabled")
        col_lect = recreate(client, "onslaught_lectures", bge_ef)
        col_para = recreate(client, "onslaught_paragraphs", bge_ef)
        lect_existing = 0
        para_existing = 0
    else:
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
            col = client.create_collection(name=name, embedding_function=bge_ef, metadata={"description": name})
            print(f"  ✅ Created {name}")
            return col, 0
        col_lect, lect_existing = get_or_create_resume("onslaught_lectures")
        col_para, para_existing = get_or_create_resume("onslaught_paragraphs")

    print("\n⚙️  Embedding lectures…")
    if lect_existing < len(lecture_docs):
        add_docs(col_lect, lecture_docs[lect_existing:], lecture_meta[lect_existing:], batch=args.batch, start_index=lect_existing)
    else:
        print("  ✅ lectures up-to-date")

    print("⚙️  Embedding paragraphs…")
    if para_existing < len(para_docs):
        add_docs(col_para, para_docs[para_existing:], para_meta[para_existing:], batch=args.batch, start_index=para_existing)
    else:
        print("  ✅ paragraphs up-to-date")

    print("\n📊 Final counts:")
    print(f"  onslaught_lectures   : {col_lect.count()}")
    print(f"  onslaught_paragraphs : {col_para.count()}")
    print("\n✅ Total Onslaught ingest complete.")


if __name__ == "__main__":
    main()

