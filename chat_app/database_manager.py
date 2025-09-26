from __future__ import annotations

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import sys

import os

from .config import (
    DB_PATH,
    KJV_VERSES_JSON,
    WEB_VERSES_JSON,
    STRONGS_NUMBERS_JSON,
    STRONGS_WORD_SUMMARIES_JSON,
)


# Make scripts/ importable for RetrievalRouter
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
from scripts.retrieval_router import RetrievalRouter  # type: ignore


@dataclass
class ConcordanceResult:
    source: str
    osis_id: Optional[str]
    text: str
    metadata: Dict[str, Any]


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.client: Optional[Any] = None
        self.router = RetrievalRouter()
        self.kjv_by_osis: Dict[str, Dict] = {}
        self.web_by_osis: Dict[str, Dict] = {}
        self.strongs_by_num: Dict[str, Dict] = {}
        self.word_to_strongs: Dict[str, List[str]] = {}
        self.embedding_model: Optional[Any] = None
        self.device: str = "cpu"
        # Try to prepare an embedding model, but don't crash if unavailable
        try:
            # Avoid accidental network calls in restricted environments
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer  # type: ignore
            # Select device automatically
            try:
                import torch  # type: ignore
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                # ROCm shows up under torch.cuda on ROCm builds; capture HIP version if present
                self.torch_hip = getattr(torch.version, "hip", None)
            except Exception:
                self.device = "cpu"
                self.torch_hip = None
            # Use the same embedding model as ingestion (BGE-large, 1024-dim)
            self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5", device=self.device)
        except Exception:
            # Will fall back to query_texts if Chroma supports it, else no vector search
            self.embedding_model = None
            self.torch_hip = None

    def connect(self) -> None:
        if self.client is not None:
            return
        try:
            import chromadb  # type: ignore
            self.client = chromadb.PersistentClient(path=str(self.db_path))
        except Exception:
            self.client = None

    def load_fast_lookup(self) -> None:
        # KJV
        if KJV_VERSES_JSON.exists():
            with KJV_VERSES_JSON.open() as f:
                data = json.load(f)
                for c in data.get("chunks", []):
                    self.kjv_by_osis[c["osis_id"]] = c
        # WEB
        if WEB_VERSES_JSON.exists():
            with WEB_VERSES_JSON.open() as f:
                data = json.load(f)
                for c in data.get("chunks", []):
                    self.web_by_osis[c["osis_id"]] = c
        # Strong's numbers
        if STRONGS_NUMBERS_JSON.exists():
            with STRONGS_NUMBERS_JSON.open() as f:
                for item in json.load(f):
                    sn = item.get("metadata", {}).get("strong_number")
                    if sn:
                        self.strongs_by_num[sn.upper()] = item
        # Strong's word summaries (map English words to top Strong's numbers)
        if STRONGS_WORD_SUMMARIES_JSON.exists():
            try:
                with STRONGS_WORD_SUMMARIES_JSON.open() as f:
                    for item in json.load(f):
                        content = (item.get("content") or "").strip()
                        # Expect patterns like: "Word 'FAITH' — ... Top Strong's: Hxxxx, Gxxxx"
                        import re
                        mword = re.search(r"Word\s+'([^']+)'", content)
                        mtop = re.search(r"Top Strong's:\s*([HG]\d+(?:\s*,\s*[HG]?\d+)*)", content)
                        if mword and mtop:
                            w = mword.group(1).strip().upper()
                            nums = [n.strip() if n[0] in ('H','G') else ('H'+n.strip()) for n in mtop.group(1).split(',')]
                            # Normalize to include H/G prefix
                            norm = []
                            for n in nums:
                                n = n.strip().upper()
                                if not n:
                                    continue
                                if n[0] not in ('H','G'):
                                    n = 'H' + n
                                norm.append(n)
                            if norm:
                                self.word_to_strongs[w] = norm
            except Exception:
                # Non-fatal
                pass

    # Retrieval function used by router
    def _retrieve_from_collection(self, collection_name: str, query: str, k: int) -> List[Dict[str, Any]]:
        if not self.client:
            self.connect()
        if self.client is None:
            return []
        try:
            col = self.client.get_collection(name=collection_name)  # type: ignore
        except Exception:
            return []
        res: Dict[str, Any] = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
        try:
            if self.embedding_model is not None:
                # Keep batch_size small for interactivity
                emb = self.embedding_model.encode(query, batch_size=8).tolist()
                res = col.query(query_embeddings=[emb], n_results=k, include=["documents", "metadatas", "distances"])  # type: ignore
            else:
                # Fallback to provider-side text embedding if available
                res = col.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])  # type: ignore
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for i in range(len(docs)):
            meta = metas[i] if i < len(metas) else {}
            out.append({
                "id": ids[i] if i < len(ids) else "",
                "content": docs[i],
                "score": 1.0 - (dists[i] if i < len(dists) else 0.0),
                "metadata": meta,
            })
        return out

    def device_info(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "embedding_device": getattr(self, "device", "cpu"),
            "embedding_model_loaded": self.embedding_model is not None,
        }
        try:
            import torch  # type: ignore
            info.update({
                "torch_cuda_available": bool(torch.cuda.is_available()),
                "torch_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "torch_hip_version": getattr(torch.version, "hip", None),
            })
        except Exception:
            info.update({
                "torch_cuda_available": False,
                "torch_device_name": None,
                "torch_hip_version": None,
            })
        return info

    def routed_search(self, query: str) -> List[Dict[str, Any]]:
        results = self.router.route_query(query, self._retrieve_from_collection)
        out = []
        for r in results:
            out.append({
                "id": r.id,
                "osis_id": r.osis_id,
                "content": r.content,
                "score": r.score,
                "source_layer": r.source_layer,
                "metadata": r.metadata,
            })
        return out

    def verse_lookup(self, osis_id: str) -> List[ConcordanceResult]:
        res: List[ConcordanceResult] = []
        if osis_id in self.kjv_by_osis:
            item = self.kjv_by_osis[osis_id]
            res.append(ConcordanceResult(source="KJV", osis_id=osis_id, text=item["content"], metadata=item.get("metadata", {})))
        if osis_id in self.web_by_osis:
            item = self.web_by_osis[osis_id]
            res.append(ConcordanceResult(source="WEB", osis_id=osis_id, text=item["content"], metadata=item.get("metadata", {})))
        return res

    def strongs_lookup(self, number: str) -> Optional[Dict[str, Any]]:
        num = number.strip().upper()
        if num.startswith("H") or num.startswith("G"):
            return self.strongs_by_num.get(num)
        return self.strongs_by_num.get(f"H{num}") or self.strongs_by_num.get(f"G{num}")

    def stats(self) -> Dict[str, Any]:
        stats = {}
        try:
            if not self.client:
                self.connect()
            assert self.client is not None
            for name in [
                "kjv_verses", "kjv_pericopes", "kjv_chapters",
                "web_verses", "web_pericopes", "web_chapters",
                "strongs_concordance_entries",
                "sop_paragraphs", "sop_chapters",
            ]:
                try:
                    col = self.client.get_collection(name)
                    stats[name] = col.count()
                except Exception:
                    continue
        except Exception:
            pass
        stats["kjv_cached_verses"] = len(self.kjv_by_osis)
        stats["web_cached_verses"] = len(self.web_by_osis)
        stats["strongs_cached_numbers"] = len(self.strongs_by_num)
        stats["word_to_strongs"] = len(self.word_to_strongs)
        return stats

    def lexical_search(self, term: str) -> List[Dict[str, Any]]:
        """Case-insensitive substring search over KJV/WEB verse caches.

        Returns a list of rows with: {osis_id, source, text} one row per translation match.
        """
        t = term.strip()
        if not t:
            return []
        t_low = t.lower()
        results: List[Dict[str, Any]] = []

        # Search KJV
        for osis_id, item in self.kjv_by_osis.items():
            txt = item.get("content", "")
            if t_low in txt.lower():
                results.append({
                    "osis_id": osis_id,
                    "source": "KJV",
                    "text": txt,
                })

        # Search WEB
        for osis_id, item in self.web_by_osis.items():
            txt = item.get("content", "")
            if t_low in txt.lower():
                results.append({
                    "osis_id": osis_id,
                    "source": "WEB",
                    "text": txt,
                })

        # Sort by OSIS id then source for stable pagination
        results.sort(key=lambda r: (r["osis_id"], r["source"]))
        return results

    def get_strongs_for_keyword(self, term: str) -> List[str]:
        t = (term or "").strip().upper()
        if not t:
            return []
        return self.word_to_strongs.get(t, [])

    def get_strongs_entries(self, numbers: List[str]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for n in numbers:
            key = n.upper()
            entry = self.strongs_by_num.get(key)
            if not entry:
                continue
            content = (entry.get("content") or "").strip()
            # Prefer definition block before '---'
            def_block = content.split("---", 1)[0].strip()

            # Attempt to parse lemma + transliteration line (e.g., "1813 exaleipho ex-al-i'-fo")
            lemma = ""
            translit = ""
            import re
            lines = [ln.strip() for ln in def_block.splitlines() if ln.strip()]
            # Find a line that starts with a number then words
            for ln in lines:
                m = re.match(r"^(\d+)\s+([A-Za-z][A-Za-z\-']*)\s+(.+)$", ln)
                if m:
                    lemma = m.group(2)
                    translit = m.group(3).strip()
                    break

            language = "Hebrew" if key.startswith('H') else ("Greek" if key.startswith('G') else "")

            # Build a concise definition snippet (first 1-3 lines after lemma line)
            snippet_lines: List[str] = []
            started = False
            for ln in lines:
                if not started:
                    # Skip until after lemma line
                    if lemma and lemma in ln:
                        started = True
                    continue
                # Stop at next header-style line or if we have enough
                if len(snippet_lines) >= 3:
                    break
                snippet_lines.append(ln)
            snippet = " ".join(snippet_lines).strip() or def_block

            out.append({
                "number": key,
                "language": language,
                "lemma": lemma,
                "transliteration": translit,
                "definition": snippet,
            })
        return out
