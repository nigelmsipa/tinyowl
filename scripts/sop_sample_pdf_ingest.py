#!/usr/bin/env python3
"""
SOP PDF Sample Ingest (paragraphs) — Desire of Ages

Embeds a sample of paragraphs from DesireofAges.pdf into a temporary
collection for quick quality validation before full SOP ingestion.

Collections:
  - sop_sample_pdf_da_paragraphs

Non-destructive. Recreates the sample collection each run.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import re

import chromadb
from chromadb.utils import embedding_functions

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
VDB_PATH = str(ROOT / "vectordb")
PDF_PATH = ROOT / "domains/theology/raw/DesireofAges.pdf"
COLL = "sop_sample_pdf_da_paragraphs"


FRONT_MATTER_PATTERNS = (
    re.compile(r"Ellen G\. White Estate", re.I),
    re.compile(r"Information about this Book", re.I),
    re.compile(r"Overview", re.I),
    re.compile(r"This ePub publication is provided", re.I),
)


def extract_pdf_paragraphs(path: Path, max_pages: int = 120) -> List[str]:
    raw = ""
    # First try pypdf if available
    if PdfReader is not None:
        try:
            rd = PdfReader(str(path))
            texts: List[str] = []
            for i, pg in enumerate(rd.pages):
                if i >= max_pages:
                    break
                t = (pg.extract_text() or "").replace("\r\n", "\n").replace("\r", "\n")
                texts.append(t)
            raw = "\n".join(texts)
        except Exception:
            raw = ""
    # Fallback to system pdftotext for robust extraction
    if not raw.strip():
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=True) as tmp:
            try:
                # Use -l to limit pages
                subprocess.run(["pdftotext", "-layout", "-l", str(max_pages), str(path), tmp.name], check=True)
                raw = Path(tmp.name).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                raw = ""
    # Normalize and split paragraphs
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    paras = [p.strip() for p in raw.split("\n\n")]
    out: List[str] = []
    for p in paras:
        if len(p) < 80:
            continue
        if any(rx.search(p) for rx in FRONT_MATTER_PATTERNS):
            continue
        out.append(p)
    # Heuristic fallback: build paragraphs from single-line breaks
    if not out:
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        buf: List[str] = []
        def flush():
            if not buf:
                return
            para = " ".join(buf).strip()
            if len(para) >= 80 and not any(rx.search(para) for rx in FRONT_MATTER_PATTERNS):
                out.append(para)
            buf.clear()
        for ln in lines:
            buf.append(ln)
            if len(" ".join(buf)) >= 500 or ln.endswith(('.', '?', '!')):
                flush()
        flush()
    return out


def recreate_collection(client: chromadb.ClientAPI, name: str, ef) -> chromadb.Collection:
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.create_collection(name=name, embedding_function=ef, metadata={"description": name})


def add_in_batches(col, docs: List[str], book: str, batch: int = 64) -> int:
    count = 0
    ids: List[str] = []
    metas: List[Dict] = []
    for i, d in enumerate(docs):
        ids.append(f"{col.name}_{i}")
        metas.append({"source": "sop", "book": book, "unit": "paragraph", "index": i})
        if len(ids) >= batch:
            col.add(ids=ids, documents=docs[count:count+len(ids)], metadatas=metas)
            count += len(ids)
            ids, metas = [], []
    if ids:
        col.add(ids=ids, documents=docs[count:count+len(ids)], metadatas=metas)
        count += len(ids)
    return count


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"PDF not found: {PDF_PATH}")
    print("🧪 SOP PDF Sample — Desire of Ages")
    print("PDF:", PDF_PATH)

    print("\n📖 Extracting/cleaning paragraphs…")
    paras = extract_pdf_paragraphs(PDF_PATH, max_pages=120)
    print(f"  Paragraphs (sampled): {len(paras)}")
    sample = paras[:400]

    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='BAAI/bge-large-en-v1.5')
    client = chromadb.PersistentClient(path=VDB_PATH)
    print("\n🗃️  Recreating collection…")
    col = recreate_collection(client, COLL, bge_ef)
    print("⚙️  Embedding…")
    n = add_in_batches(col, sample, "Desire of Ages")
    print(f"📊 Added: {n} paragraphs")

    probes = [
        "Sermon on the Mount",
        "healing the sick",
        "Pharisees and traditions",
        "compassion of Christ",
    ]
    print("\n🔎 Probe results:")
    for q in probes:
        r = col.query(query_texts=[q], n_results=3, include=["documents", "metadatas", "distances"])  # type: ignore
        docs = (r.get("documents") or [[]])[0]
        dists = (r.get("distances") or [[]])[0]
        print(f"\nQuery: {q}")
        for i in range(len(docs)):
            sc = 1.0 - (dists[i] if i < len(dists) else 0.0)
            print(f"  - {sc:.3f} | {(docs[i] or '').replace('\n',' ')[:160]}")
    print("\n✅ SOP PDF sample complete. Inspect above to confirm quality.")


if __name__ == "__main__":
    main()
