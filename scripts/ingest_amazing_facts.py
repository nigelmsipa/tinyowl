#!/usr/bin/env python3
"""
Ingest "Amazing Facts" PDFs (paragraph + chapter layers) into TinyOwl's ChromaDB.

Collections:
  - amazing_paragraphs
  - amazing_chapters

Matches SOP/Secrets pipelines for consistency.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict
import re
import sys

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).resolve().parents[1]
VDB_PATH = str(ROOT / "vectordb")
BACKUP_DIR = str(ROOT / "backups")

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))
try:
    from safety import backup_collection as _backup_collection  # type: ignore
except Exception:
    _backup_collection = None

DEFAULT_SRC = Path.home() / "Downloads" / "Amazing Facts"

try:
    from pypdf import PdfReader  # type: ignore
except Exception:
    PdfReader = None  # type: ignore

FRONT_MATTER_PATTERNS = (
    re.compile(r"table of contents", re.I),
    re.compile(r"copyright", re.I),
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
                import subprocess as sp
                sp.run(cmd, check=True)
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
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    buf: List[str] = []
    res: List[str] = []
    def flush():
        if not buf:
            return
        para = " ".join(buf).strip()
        if len(para) >= 120 and not any(rx.search(para) for rx in FRONT_MATTER_PATTERNS):
            res.append(para)
        buf.clear()
    for ln in lines:
        buf.append(ln)
        if len(" ".join(buf)) >= 600 or ln.endswith(('.', '!', '?')):
            flush()
    flush()
    return res


def chapterize(raw: str) -> List[str]:
    blocks: List[str] = []
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    cur: List[str] = []
    header = re.compile(r"^(?:CHAPTER|Chapter)\s+\d+|^\s*[IVXLC]+\.?\s*$")
    for ln in lines:
        if header.match(ln.strip()) and cur:
            blocks.append("\n".join(cur).strip())
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip())
    blocks = [b for b in blocks if len(b) >= 800 and not any(rx.search(b) for rx in FRONT_MATTER_PATTERNS)]
    if blocks:
        return blocks
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
    ap = argparse.ArgumentParser(description="Ingest Amazing Facts PDFs into paragraph/chapter collections")
    ap.add_argument("--src", type=str, default=str(DEFAULT_SRC), help="Path to 'Amazing Facts' folder")
    ap.add_argument("--recreate", action="store_true", help="Backup + recreate collections before embedding")
    ap.add_argument("--batch", type=int, default=96, help="Embedding batch size")
    args = ap.parse_args()

    src_dir = Path(args.src)
    if not src_dir.exists():
        raise SystemExit(f"Source directory not found: {src_dir}")

    files = sorted(p for p in src_dir.glob("*.pdf"))
    if not files:
        raise SystemExit("No PDFs found in source directory")

    print(f"🦉 Amazing Facts ingest: {len(files)} files from {src_dir}")

    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='BAAI/bge-large-en-v1.5')
    client = chromadb.PersistentClient(path=VDB_PATH)

    print("\n🗃️  Preparing collections…")
    if args.recreate:
        print("  ♻️  Recreate mode enabled")
        col_par = recreate(client, "amazing_paragraphs", bge_ef)
        col_chp = recreate(client, "amazing_chapters", bge_ef)
        par_existing = 0
        chp_existing = 0
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
        col_par, par_existing = get_or_create_resume("amazing_paragraphs")
        col_chp, chp_existing = get_or_create_resume("amazing_chapters")

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
            for i, p in enumerate(paras):
                all_par_docs.append(p)
                all_par_meta.append({
                    "source": "amazing_facts",
                    "book": book,
                    "unit": "paragraph",
                    "index": i,
                    "file": path.name,
                })
            for i, c in enumerate(chaps):
                all_chp_docs.append(c)
                all_chp_meta.append({
                    "source": "amazing_facts",
                    "book": book,
                    "unit": "chapter",
                    "index": i,
                    "file": path.name,
                })
            print(f"  ➕ paragraphs: {len(paras)} | chapters: {len(chaps)}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue

    chunks_dir = ROOT / "domains/theology/chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    (chunks_dir / "amazing_paragraphs.json").write_text(
        __import__('json').dumps(all_par_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (chunks_dir / "amazing_chapters.json").write_text(
        __import__('json').dumps(all_chp_docs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n💾 Saved chunk lists: amazing_paragraphs.json ({len(all_par_docs)}), amazing_chapters.json ({len(all_chp_docs)})")

    print("\n⚙️  Embedding paragraphs…")
    if par_existing < len(all_par_docs):
        add_docs(col_par, all_par_docs[par_existing:], all_par_meta[par_existing:], batch=args.batch, start_index=par_existing)
    else:
        print("  ✅ Up-to-date")
    print("⚙️  Embedding chapters…")
    if chp_existing < len(all_chp_docs):
        add_docs(col_chp, all_chp_docs[chp_existing:], all_chp_meta[chp_existing:], batch=args.batch, start_index=chp_existing)
    else:
        print("  ✅ Up-to-date")

    print("\n📊 Final counts:")
    print(f"  amazing_paragraphs: {col_par.count()}")
    print(f"  amazing_chapters  : {col_chp.count()}")
    print("\n✅ Amazing Facts ingest complete.")


if __name__ == "__main__":
    main()

