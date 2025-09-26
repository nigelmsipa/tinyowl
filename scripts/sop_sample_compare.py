#!/usr/bin/env python3
"""
Compare SOP ingestion quality: PDF vs Markdown (sample-only, non-destructive).

What it does:
- Reads a chosen SOP book from both PDF and MD in Downloads
- Splits into paragraphs (sample subset)
- Embeds into two temporary Chroma collections:
    sop_sample_pdf_desire, sop_sample_md_desire
- Runs a few probe queries and prints top hits for quick eyeballing

Safe to run multiple times; collections are recreated each run.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Tuple

import chromadb
from chromadb.utils import embedding_functions

try:
    from pypdf import PdfReader
except Exception as e:  # pragma: no cover
    raise SystemExit("pypdf not available in venv")


ROOT = Path(__file__).resolve().parents[1]
VDB_PATH = str(ROOT / "vectordb")

# Input files (adjust here if needed)
PDF_PATH = Path.home() / "Downloads/Spirit Of Prophecy (1)-20250925T083805Z-1-001/Spirit Of Prophecy (1)/Child Guidance (1).pdf"
MD_PATH = Path.home() / "Downloads/NoteBook_Spirit of prophecy/Source_Child Guidance (1).pdf.md"

PDF_COLLECTION = "sop_sample_pdf_child"
MD_COLLECTION = "sop_sample_md_child"


def read_pdf_paragraphs(path: Path, max_pages: int = 80) -> List[str]:
    reader = PdfReader(str(path))
    parts: List[str] = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        txt = page.extract_text() or ""
        parts.append(txt)
    full = "\n".join(parts)
    return split_paragraphs(full)


def read_md_paragraphs(path: Path, max_chars: int = 120_000) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) > max_chars:
        text = text[:max_chars]
    return split_paragraphs(text)


def split_paragraphs(text: str) -> List[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    # Prefer blank-line separated paragraphs; fallback to dense lines
    paras = [p.strip() for p in raw.split("\n\n")]
    paras = [p for p in paras if len(p) >= 60]
    return paras


def build_documents(paras: List[str], fmt: str, book: str, limit: int = 400) -> Tuple[List[str], List[Dict]]:
    docs: List[str] = []
    metas: List[Dict] = []
    for i, p in enumerate(paras[:limit]):
        docs.append(p)
        metas.append({
            "source": "sop_sample",
            "format": fmt,
            "book": book,
            "para_index": i,
        })
    return docs, metas


def recreate_collection(client: chromadb.ClientAPI, name: str, ef) -> chromadb.Collection:
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.create_collection(name=name, embedding_function=ef, metadata={"description": name})


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"PDF not found: {PDF_PATH}")
    if not MD_PATH.exists():
        raise SystemExit(f"MD not found:  {MD_PATH}")

    print("🧪 SOP Sample Compare: Desire of Ages (PDF vs MD)")
    print("PDF:", PDF_PATH)
    print("MD: ", MD_PATH)

    print("\n📖 Extracting paragraphs…")
    pdf_paras = read_pdf_paragraphs(PDF_PATH)
    md_paras = read_md_paragraphs(MD_PATH)
    print(f"  PDF paragraphs: {len(pdf_paras)} (sampled)")
    print(f"  MD  paragraphs: {len(md_paras)} (sampled)")

    pdf_docs, pdf_meta = build_documents(pdf_paras, fmt="pdf", book="Child Guidance")
    md_docs, md_meta = build_documents(md_paras, fmt="md", book="Child Guidance")

    # Use BGE-large for embeddings via collection embedding_function
    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='BAAI/bge-large-en-v1.5')
    client = chromadb.PersistentClient(path=VDB_PATH)

    print("\n🗃️  Recreating sample collections…")
    pdf_col = recreate_collection(client, PDF_COLLECTION, bge_ef)
    md_col = recreate_collection(client, MD_COLLECTION, bge_ef)

    def add_in_batches(col, docs, metas, batch=64):
        ids = []
        for i in range(0, len(docs), batch):
            j = min(i + batch, len(docs))
            chunk_ids = [f"{col.name}_{k}" for k in range(i, j)]
            col.add(ids=chunk_ids, documents=docs[i:j], metadatas=metas[i:j])
            ids.extend(chunk_ids)
        return ids

    print("\n⚙️  Embedding PDF sample…")
    add_in_batches(pdf_col, pdf_docs, pdf_meta)
    print("⚙️  Embedding MD sample…")
    add_in_batches(md_col, md_docs, md_meta)

    print("\n📊 Collection sizes:")
    print(f"  {PDF_COLLECTION}: {pdf_col.count()}")
    print(f"  {MD_COLLECTION}:  {md_col.count()}")

    # Probe queries indicative of DA topics
    probes = [
        "Christian parenting",
        "discipline with love",
        "home education",
        "character building",
    ]

    def top_snippets(col, q, n=3):
        r = col.query(query_texts=[q], n_results=n, include=["documents", "metadatas", "distances"])  # type: ignore
        out = []
        docs = (r.get("documents") or [[]])[0]
        metas = (r.get("metadatas") or [[]])[0]
        dists = (r.get("distances") or [[]])[0]
        for i in range(len(docs)):
            out.append((1.0 - (dists[i] if i < len(dists) else 0.0), (docs[i] or "").replace("\n", " ")[:160], metas[i]))
        return out

    print("\n🔎 Probe results (PDF vs MD):")
    for q in probes:
        print(f"\nQuery: {q}")
        p = top_snippets(pdf_col, q)
        m = top_snippets(md_col, q)
        print("  PDF:")
        for s, t, meta in p:
            print(f"    - {s:.3f} | {t}")
        print("  MD:")
        for s, t, meta in m:
            print(f"    - {s:.3f} | {t}")

    print("\n✅ Sample compare complete. Review above snippets to decide PDF vs MD.")


if __name__ == "__main__":
    main()
