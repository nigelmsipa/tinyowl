from __future__ import annotations

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import sys

import os
import re

import numpy as np

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
        self.word_summary_docs: Dict[str, str] = {}
        self.embedding_model: Optional[Any] = None
        self.reranker: Optional[Any] = None  # Cross-encoder for reranking
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
                            if content:
                                self.word_summary_docs[w] = content
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

    def routed_search(self, query: str, use_reranking: bool = True) -> List[Dict[str, Any]]:
        """
        Execute routed search with query enhancement, hybrid search, and reranking

        Args:
            query: User query
            use_reranking: Whether to use cross-encoder reranking (slower but better)

        Returns:
            List of ranked search results
        """
        # Pass hybrid search and reranking functions to router
        results = self.router.route_query(
            query,
            self._retrieve_from_collection,
            hybrid_search_function=self.hybrid_search,
            rerank_function=self.rerank_with_cross_encoder if use_reranking else None
        )

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

    def semantic_word_search(self, word: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find semantically similar words using vector embeddings.

        Returns a list of words ranked by semantic similarity with their similarity scores.
        """
        if not self.client:
            self.connect()
        if self.client is None:
            return []

        try:
            # Ensure we have the embedding model loaded
            if not self.embedding_model:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5", device=self.device)

            query_embedding = self.embedding_model.encode([word], show_progress_bar=False)[0]

            # Prefer definitional summaries; fall back to concordance if unavailable
            collections_to_try = [
                "strongs_word_summaries",
                "strongs_concordance_entries",
            ]

            stop_words = {"the", "and", "of", "to", "in", "a", "is", "that", "it", "for",
                          "be", "with", "as", "by", "on", "not", "he", "this", "from",
                          "but", "they", "have", "was", "his", "which", "their", "said",
                          "if", "will", "all", "were", "when", "there", "been", "has",
                          "or", "an", "had", "are", "you", "her", "them", "him", "me",
                          "my", "i", "she", "your", "we", "so", "at", "one", "into"}

            word_scores: Dict[str, float] = {}

            for collection_name in collections_to_try:
                try:
                    col = self.client.get_collection(name=collection_name)
                except Exception:
                    continue

                try:
                    results = col.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=min(200, col.count()),
                        include=["documents", "distances", "metadatas"],
                    )
                except Exception:
                    continue

                found_any = False
                for doc_list, dist_list, meta_list in zip(
                    results.get("documents", [[]]),
                    results.get("distances", [[]]),
                    results.get("metadatas", [[]])
                ):
                    for doc, dist, meta in zip(doc_list, dist_list, meta_list):
                        candidate_word = meta.get("word", "").lower().strip()

                        if not candidate_word or candidate_word == word.lower():
                            continue

                        if candidate_word in stop_words or len(candidate_word) < 3:
                            continue

                        similarity = 1 / (1 + dist)

                        if candidate_word not in word_scores or similarity > word_scores[candidate_word]:
                            word_scores[candidate_word] = similarity
                            found_any = True

                if found_any and collection_name == "strongs_word_summaries":
                    # Prefer definitional summaries; stop once we have matches from this layer
                    break

            sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)

            return [
                {"word": w, "similarity": round(score, 3)}
                for w, score in sorted_words[:limit]
            ]

        except Exception:
            return []

    def hybrid_search(self, query: str, collection_name: str = "kjv_verses", k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic vector search + keyword matching

        Best for biblical phrases and specific terms where exact matching matters.

        Args:
            query: Search query
            collection_name: ChromaDB collection to search
            k: Number of results to return

        Returns:
            Merged and reranked results from both methods
        """
        # Get semantic results from vector search
        semantic_results = self._retrieve_from_collection(collection_name, query, k)

        # Get keyword results from lexical search
        keyword_results = self.lexical_search(query)[:k]

        # Convert keyword results to same format as semantic results
        keyword_formatted = []
        for i, kr in enumerate(keyword_results):
            keyword_formatted.append({
                "id": kr.get("osis_id", f"keyword_{i}"),
                "content": kr.get("text", ""),
                "score": 0.8,  # High base score for exact keyword matches
                "metadata": {"osis_id": kr.get("osis_id"), "source": kr.get("source")},
            })

        # Merge using RRF (Reciprocal Rank Fusion)
        return self._merge_results_rrf(semantic_results, keyword_formatted, k)

    def _merge_results_rrf(self,
                          semantic_results: List[Dict[str, Any]],
                          keyword_results: List[Dict[str, Any]],
                          top_k: int,
                          k: int = 60) -> List[Dict[str, Any]]:
        """
        Merge semantic and keyword results using Reciprocal Rank Fusion

        Args:
            semantic_results: Results from vector search
            keyword_results: Results from keyword search
            top_k: Number of results to return
            k: RRF parameter (typically 60)

        Returns:
            Merged and reranked results
        """
        fused_scores: Dict[str, float] = {}
        all_results: Dict[str, Dict[str, Any]] = {}

        # Weight semantic results
        for rank, result in enumerate(semantic_results):
            result_id = result.get("id", "")
            if not result_id:
                continue

            all_results[result_id] = result
            rrf_score = 0.6 * (1.0 / (k + rank + 1))  # 60% weight to semantic
            fused_scores[result_id] = fused_scores.get(result_id, 0) + rrf_score

        # Weight keyword results (higher for exact matches)
        for rank, result in enumerate(keyword_results):
            result_id = result.get("id", "")
            if not result_id:
                continue

            if result_id not in all_results:
                all_results[result_id] = result

            rrf_score = 0.4 * (1.0 / (k + rank + 1))  # 40% weight to keyword
            fused_scores[result_id] = fused_scores.get(result_id, 0) + rrf_score

        # Sort by fused score
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

        # Build final results
        merged = []
        for result_id in sorted_ids[:top_k]:
            result = all_results[result_id]
            result["score"] = fused_scores[result_id]
            merged.append(result)

        return merged

    def rerank_with_cross_encoder(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder for better relevance

        Much more accurate than bi-encoder (BGE) but slower.
        Use after initial retrieval to refine top results.

        Args:
            query: Original query
            results: Initial retrieval results
            top_k: Number of results to return after reranking

        Returns:
            Reranked results with cross-encoder scores
        """
        if not results:
            return []

        # Lazy load cross-encoder
        if self.reranker is None:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore
                # Use lightweight cross-encoder (40MB model)
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            except Exception:
                # Fall back to original results if cross-encoder unavailable
                return results[:top_k]

        try:
            # Prepare query-document pairs for reranking
            pairs = []
            for r in results[:20]:  # Only rerank top 20 to save time
                content = r.get("content", "")[:512]  # Limit length for speed
                pairs.append([query, content])

            # Get cross-encoder scores
            scores = self.reranker.predict(pairs)

            # Update scores
            for i, r in enumerate(results[:20]):
                r["rerank_score"] = float(scores[i])
                r["original_score"] = r.get("score", 0.0)

            # Sort by reranked scores
            results[:20] = sorted(results[:20], key=lambda x: x.get("rerank_score", 0), reverse=True)

            return results[:top_k]

        except Exception:
            # Fall back to original results on error
            return results[:top_k]

    def concept_word_search(self, expression: str, limit: int = 10) -> Dict[str, Any]:
        """Compute a concept vector from +/- words and return nearest definitional neighbours."""
        if not self.client:
            self.connect()
        if self.client is None:
            return {"results": [], "positives": [], "negatives": []}

        if not self.embedding_model:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5", device=self.device)
            except Exception:
                return {"results": [], "positives": [], "negatives": []}

        tokens = re.findall(r'([+-]?)\s*([^,]+)', expression.replace(',', ' '))

        positives: List[str] = []
        negatives: List[str] = []

        def add_token(sign_char: str, token: str) -> None:
            token = token.strip()
            if not token:
                return
            normalized = token.upper()
            if normalized in self.word_summary_docs or normalized in self.word_to_strongs:
                if sign_char == '-':
                    negatives.append(normalized)
                else:
                    positives.append(normalized)
                return

            inner_parts = re.split(r'([+-])', token)
            if len(inner_parts) > 1:
                current_sign = sign_char if sign_char in ('+', '-') else '+'
                buffer = ''
                for part in inner_parts:
                    if part in ('+', '-'):
                        if buffer.strip():
                            add_token(current_sign, buffer)
                        current_sign = part
                        buffer = ''
                    else:
                        buffer += part
                if buffer.strip():
                    add_token(current_sign, buffer)
                return

            filtered = re.sub(r"[^A-Za-z0-9'\-]+", '', token)
            if not filtered:
                return
            final = filtered.upper()
            if final in self.word_summary_docs or final in self.word_to_strongs:
                if sign_char == '-':
                    negatives.append(final)
                else:
                    positives.append(final)
                return
            if sign_char == '-':
                negatives.append(final)
            else:
                positives.append(final)

        if not tokens:
            add_token('+', expression)
        else:
            for sign, token in tokens:
                add_token('-' if sign == '-' else '+', token)

        def dedupe(seq: List[str]) -> List[str]:
            seen = set()
            out = []
            for item in seq:
                if item in seen:
                    continue
                seen.add(item)
                out.append(item)
            return out

        positives = dedupe(positives)
        negatives = dedupe(negatives)

        if not positives and not negatives:
            return {"results": [], "positives": [], "negatives": []}

        def lookup_text(word: str) -> str:
            return self.word_summary_docs.get(word.upper(), word)

        def encode_words(words: List[str]) -> Optional[np.ndarray]:
            if not words:
                return None
            texts = [lookup_text(w) for w in words]
            try:
                vecs = self.embedding_model.encode(texts, show_progress_bar=False)
                return np.asarray(vecs, dtype=np.float32)
            except Exception:
                return None

        pos_vecs = encode_words(positives)
        neg_vecs = encode_words(negatives)

        if pos_vecs is None and neg_vecs is None:
            return {"results": [], "positives": positives, "negatives": negatives}

        concept_vec: Optional[np.ndarray] = None
        if pos_vecs is not None:
            concept_vec = pos_vecs.mean(axis=0)
        if neg_vecs is not None:
            neg_mean = neg_vecs.mean(axis=0)
            concept_vec = -neg_mean if concept_vec is None else concept_vec - neg_mean

        if concept_vec is None:
            return {"results": [], "positives": positives, "negatives": negatives}

        try:
            collection = self.client.get_collection(name="strongs_word_summaries")
        except Exception:
            return {"results": [], "positives": positives, "negatives": negatives}

        try:
            results = collection.query(
                query_embeddings=[concept_vec.tolist()],
                n_results=min(200, collection.count()),
                include=["documents", "distances", "metadatas"],
            )
        except Exception:
            return {"results": [], "positives": positives, "negatives": negatives}

        pos_set = {w.lower() for w in positives}
        neg_set = {w.lower() for w in negatives}

        candidates: Dict[str, Dict[str, Any]] = {}

        for doc_list, dist_list, meta_list in zip(
            results.get("documents", [[]]),
            results.get("distances", [[]]),
            results.get("metadatas", [[]])
        ):
            for doc, dist, meta in zip(doc_list, dist_list, meta_list):
                candidate = meta.get("word", "").lower().strip()
                if not candidate or candidate in pos_set or candidate in neg_set:
                    continue
                similarity = 1 / (1 + dist)
                existing = candidates.get(candidate)
                if not existing or similarity > existing["similarity"]:
                    candidates[candidate] = {
                        "word": candidate,
                        "similarity": round(similarity, 3),
                    }

        sorted_items = sorted(candidates.values(), key=lambda x: x["similarity"], reverse=True)

        return {
            "results": sorted_items[:limit],
            "positives": positives,
            "negatives": negatives,
        }
