#!/usr/bin/env python3
"""
TinyOwl Retrieval Router with Reciprocal Rank Fusion (RRF)
Implements intelligent query routing across hierarchical layers
"""

import re
from typing import Dict, List, Tuple, Optional, Set, Callable, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Import query enhancement utilities
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

try:
    from chat_app.query_enhancement import expand_biblical_query, should_use_hybrid_search
except ImportError:
    # Fallback if query_enhancement not available
    def expand_biblical_query(query: str) -> str:
        return query
    def should_use_hybrid_search(query: str) -> bool:
        return False


class QueryType(Enum):
    """Types of theological queries"""
    VERSE_LOOKUP = "verse_lookup"      # Direct verse reference
    DOCTRINAL = "doctrinal"            # Theological concept
    SOP_SPECIFIC = "sop_specific"      # Spirit of Prophecy query
    TOPICAL = "topical"                # Broad topic search
    CROSS_REFERENCE = "cross_reference" # Multi-verse comparison


@dataclass
class RetrievalPlan:
    """Plan for retrieving from multiple layers"""
    query_type: QueryType
    layers: List[str]                  # Which collections to search
    k_values: Dict[str, int]           # How many results from each layer
    weights: Dict[str, float]          # Layer importance weights
    rerank_top_k: int                  # Final result count after RRF


@dataclass
class SearchResult:
    """Individual search result with metadata"""
    id: str
    osis_id: Optional[str]
    content: str
    score: float
    source_layer: str
    metadata: Dict


class RetrievalRouter:
    """Smart query router with hierarchical search and RRF fusion"""
    
    def __init__(self):
        self.verse_patterns = self._compile_verse_patterns()
        self.sop_patterns = self._compile_sop_patterns()
        self.doctrinal_keywords = self._load_doctrinal_keywords()
        # Map logical layers to actual Chroma collections in the live DB
        # Only include collections that actually exist!
        self.layer_to_collections = {
            'theology_verses': ['kjv_verses', 'web_verses'],
            'theology_pericopes': ['kjv_pericopes', 'web_pericopes'],
            'theology_chapters': ['kjv_chapters', 'web_chapters'],
            # Spirit of Prophecy (Ellen G. White)
            'sop_paragraphs': ['sop_paragraphs'],
            'sop_chapters': ['sop_chapters'],
            # NOTE: Collections below don't exist yet - commented out until ingested
            # 'commentary_paras': ['sop_paragraphs', 'secrets_paragraphs', 'amazing_paragraphs', 'threeabn_paragraphs'],
            # 'naves_topic_entries': ['naves_topic_entries'],
        }
        
    def _compile_verse_patterns(self) -> List[re.Pattern]:
        """Compile verse reference detection patterns"""
        patterns = [
            # "John 3:16", "1 Samuel 15:22"
            re.compile(r'\b(\d*\s*\w+)\s+(\d+):(\d+)(?:-(\d+))?\b', re.IGNORECASE),
            # "Genesis chapter 1", "Revelation 22"
            re.compile(r'\b(\w+)\s+(?:chapter\s+)?(\d+)\b', re.IGNORECASE),
            # Multiple references: "Romans 3:23 and John 3:16"
            re.compile(r'\b(\w+)\s+(\d+):(\d+)(?:\s+and\s+(\w+)\s+(\d+):(\d+))?\b', re.IGNORECASE)
        ]
        return patterns
    
    def _compile_sop_patterns(self) -> List[re.Pattern]:
        """Compile Spirit of Prophecy detection patterns"""
        patterns = [
            re.compile(r'\b(?:according\s+to\s+)?(?:ellen\s+white|spirit\s+of\s+prophecy|sop)\b', re.IGNORECASE),
            re.compile(r'\b(?:great\s+controversy|desire\s+of\s+ages|patriarchs\s+and\s+prophets)\b', re.IGNORECASE),
            re.compile(r'\b(?:testimonies|steps\s+to\s+christ|early\s+writings)\b', re.IGNORECASE),
            # Supporting ministries / series
            re.compile(r'\b(?:secrets\s+unsealed|amazing\s+facts|3\s*abn|3abn)\b', re.IGNORECASE),
            re.compile(r'\b(?:walter\s+veith|total\s+onslaught|doug\s+batchelor|joe\s+crews)\b', re.IGNORECASE),
        ]
        return patterns
    
    def _load_doctrinal_keywords(self) -> Set[str]:
        """Load theological/doctrinal keywords"""
        return {
            # SDA Core Doctrines
            'sanctuary', 'investigative judgment', 'sabbath', 'second coming',
            'state of the dead', 'remnant church', 'prophetic gift',
            'health message', 'tithing', 'baptism', 'lord\'s supper',

            # General Theological Terms
            'salvation', 'justification', 'sanctification', 'atonement',
            'redemption', 'grace', 'faith', 'works', 'law', 'gospel',
            'sin', 'righteousness', 'repentance', 'forgiveness',
            'trinity', 'incarnation', 'resurrection', 'eschatology',
            'prophecy', 'covenant', 'creation', 'judgment',

            # Biblical Topics
            'unpardonable sin', 'blasphemy', 'holy spirit', 'prayer',
            'worship', 'church', 'ministry', 'discipleship',
            'stewardship', 'mission', 'evangelism',

            # Messianic & Divine Titles
            'glory', 'king of glory', 'messiah', 'christ', 'lord',
            'son of god', 'son of man', 'lamb of god', 'bread of life',
            'good shepherd', 'alpha omega', 'emmanuel', 'savior'
        }
    
    def classify_query(self, query: str) -> QueryType:
        """Classify query to determine retrieval strategy"""
        query_lower = query.lower()
        
        # Check for verse references
        for pattern in self.verse_patterns:
            if pattern.search(query):
                return QueryType.VERSE_LOOKUP
        
        # Check for Spirit of Prophecy queries
        for pattern in self.sop_patterns:
            if pattern.search(query):
                return QueryType.SOP_SPECIFIC
        
        # Check for doctrinal terms
        query_words = set(query_lower.split())
        if any(keyword in query_lower for keyword in self.doctrinal_keywords):
            return QueryType.DOCTRINAL
        
        # Check for cross-reference indicators
        cross_ref_indicators = ['compare', 'cross reference', 'parallel', 'similar']
        if any(indicator in query_lower for indicator in cross_ref_indicators):
            return QueryType.CROSS_REFERENCE
        
        # Default to topical
        return QueryType.TOPICAL
    
    def create_retrieval_plan(self, query: str) -> RetrievalPlan:
        """Create retrieval plan based on query classification"""
        query_type = self.classify_query(query)
        
        if query_type == QueryType.VERSE_LOOKUP:
            return RetrievalPlan(
                query_type=query_type,
                layers=['theology_verses', 'theology_pericopes'],
                k_values={'theology_verses': 4, 'theology_pericopes': 6},
                weights={'theology_verses': 0.7, 'theology_pericopes': 0.3},
                rerank_top_k=10
            )
        
        elif query_type == QueryType.DOCTRINAL:
            # BIBLE-FIRST: Scripture primary, then Spirit of Prophecy for theological context
            return RetrievalPlan(
                query_type=query_type,
                layers=['theology_verses', 'theology_pericopes', 'sop_paragraphs', 'theology_chapters'],
                k_values={'theology_verses': 6, 'theology_pericopes': 8, 'sop_paragraphs': 6, 'theology_chapters': 4},
                weights={'theology_verses': 0.35, 'theology_pericopes': 0.30, 'sop_paragraphs': 0.25, 'theology_chapters': 0.10},
                rerank_top_k=18
            )
        
        elif query_type == QueryType.SOP_SPECIFIC:
            # SOP-FIRST: Spirit of Prophecy primary, Scripture for biblical foundation
            return RetrievalPlan(
                query_type=query_type,
                layers=['sop_paragraphs', 'sop_chapters', 'theology_pericopes', 'theology_verses'],
                k_values={'sop_paragraphs': 10, 'sop_chapters': 6, 'theology_pericopes': 4, 'theology_verses': 4},
                weights={'sop_paragraphs': 0.50, 'sop_chapters': 0.25, 'theology_pericopes': 0.15, 'theology_verses': 0.10},
                rerank_top_k=16
            )
        
        elif query_type == QueryType.CROSS_REFERENCE:
            return RetrievalPlan(
                query_type=query_type,
                layers=['theology_verses', 'theology_pericopes', 'theology_chapters'],
                k_values={'theology_verses': 6, 'theology_pericopes': 8, 'theology_chapters': 4},
                weights={'theology_verses': 0.3, 'theology_pericopes': 0.5, 'theology_chapters': 0.2},
                rerank_top_k=18
            )
        
        else:  # TOPICAL
            # BIBLE+SOP: Scripture primary, Spirit of Prophecy for theological connections
            return RetrievalPlan(
                query_type=query_type,
                layers=['theology_verses', 'theology_pericopes', 'sop_paragraphs', 'theology_chapters'],
                k_values={'theology_verses': 6, 'theology_pericopes': 8, 'sop_paragraphs': 6, 'theology_chapters': 4},
                weights={'theology_verses': 0.35, 'theology_pericopes': 0.30, 'sop_paragraphs': 0.25, 'theology_chapters': 0.10},
                rerank_top_k=16
            )
    
    def reciprocal_rank_fusion(self, 
                              results_by_layer: Dict[str, List[SearchResult]], 
                              weights: Dict[str, float],
                              k: int = 60) -> List[SearchResult]:
        """
        Implement Reciprocal Rank Fusion across multiple result sets
        
        Args:
            results_by_layer: Results from each layer
            weights: Layer importance weights
            k: RRF parameter (typically 60)
        
        Returns:
            Fused and reranked results
        """
        fused_scores = {}
        all_results = {}
        
        # Collect all unique results
        for layer, results in results_by_layer.items():
            layer_weight = weights.get(layer, 1.0)
            
            for rank, result in enumerate(results):
                result_id = result.id
                
                # Store result object
                if result_id not in all_results:
                    all_results[result_id] = result
                
                # Calculate RRF score: weight * (1 / (k + rank))
                rrf_score = layer_weight * (1.0 / (k + rank + 1))
                
                if result_id in fused_scores:
                    fused_scores[result_id] += rrf_score
                else:
                    fused_scores[result_id] = rrf_score
        
        # Sort by fused score
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # Return reranked results with updated scores
        fused_results = []
        for result_id in sorted_ids:
            result = all_results[result_id]
            result.score = fused_scores[result_id]  # Update to RRF score
            fused_results.append(result)
        
        return fused_results
    
    def simple_reranker(self, 
                       query: str, 
                       results: List[SearchResult], 
                       top_k: int) -> List[SearchResult]:
        """
        Simple rule-based reranker for final result ordering
        
        Priority rules:
        1. Exact verse matches (if query contains verse reference)
        2. Book name matches
        3. Scripture reference overlap
        4. Original retrieval score
        """
        query_lower = query.lower()
        
        # Extract query features
        has_verse_ref = any(pattern.search(query) for pattern in self.verse_patterns)
        query_books = self._extract_book_names(query)
        
        # Score adjustments
        for result in results:
            boost_score = 0
            
            # Boost exact verse matches
            if has_verse_ref and result.osis_id:
                if any(book.lower() in result.osis_id.lower() for book in query_books):
                    boost_score += 0.5
            
            # Boost book matches
            if query_books:
                for book in query_books:
                    if book.lower() in result.content.lower()[:100]:  # Check first 100 chars
                        boost_score += 0.2
            
            # Boost scripture references in metadata
            if hasattr(result, 'metadata') and 'scripture_refs' in result.metadata:
                scripture_refs = result.metadata.get('scripture_refs', [])
                if any(book.lower() in ref.lower() for book in query_books for ref in scripture_refs):
                    boost_score += 0.3
            
            # Apply boost
            result.score += boost_score
        
        # Sort by final score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _extract_book_names(self, query: str) -> List[str]:
        """Extract potential book names from query"""
        book_names = []
        
        # Common book name patterns
        book_patterns = [
            r'\b(Genesis|Exodus|Leviticus|Numbers|Deuteronomy)\b',
            r'\b(\d*\s*Samuel|Kings|Chronicles)\b',
            r'\b(Matthew|Mark|Luke|John|Acts|Romans)\b',
            r'\b(Corinthians|Galatians|Ephesians|Philippians)\b',
            r'\b(Colossians|Thessalonians|Timothy|Titus)\b',
            r'\b(Hebrews|James|Peter|John|Jude|Revelation)\b'
        ]
        
        for pattern in book_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            book_names.extend(matches)
        
        return book_names
    
    def route_query(self,
                   query: str,
                   retrieval_function,
                   hybrid_search_function: Optional[Callable[[str, str, int], List[Any]]] = None,
                   rerank_function: Optional[Callable[[str, List[Any], int], List[Any]]] = None) -> List[SearchResult]:
        """
        Main routing function - orchestrates the entire retrieval process

        Args:
            query: User query
            retrieval_function: Function to perform actual vector search
                               Should accept (collection_name, query, k) and return results
            hybrid_search_function: Optional function for hybrid search (semantic + keyword)
            rerank_function: Optional function for cross-encoder reranking

        Returns:
            Final ranked results ready for response generation
        """
        # Expand query with biblical phrases if applicable
        expanded_query = expand_biblical_query(query)

        # Use expanded query for retrieval
        search_query = expanded_query

        # Determine if we should use hybrid search
        use_hybrid = should_use_hybrid_search(query) and hybrid_search_function is not None

        # Create retrieval plan
        plan = self.create_retrieval_plan(query)
        
        # Execute searches across layers
        results_by_layer = {}
        for layer in plan.layers:
            k_for_layer = plan.k_values[layer]
            merged_results: List[SearchResult] = []
            collections = self.layer_to_collections.get(layer, [layer])

            for col in collections:
                # Use hybrid search for Bible verse layers (better for exact phrase matching)
                bible_verse_collections = {'theology_verses', 'kjv_verses', 'web_verses', 'kjv_pericopes', 'web_pericopes'}
                if use_hybrid and col in bible_verse_collections and hybrid_search_function:
                    sub_results = hybrid_search_function(search_query, col, max(1, k_for_layer // max(1, len(collections))))
                else:
                    sub_results = retrieval_function(col, search_query, max(1, k_for_layer // max(1, len(collections))))

                # Convert to SearchResult format if needed
                if sub_results and not isinstance(sub_results[0], SearchResult):
                    sub_results = [
                        SearchResult(
                            id=r.get('id', ''),
                            osis_id=r.get('metadata', {}).get('osis_id'),
                            content=r.get('content', ''),
                            score=r.get('score', 0.0),
                            source_layer=layer,
                            metadata=r.get('metadata', {})
                        )
                        for r in sub_results
                    ]
                merged_results.extend(sub_results or [])

            results_by_layer[layer] = merged_results
        
        # Apply RRF fusion
        fused_results = self.reciprocal_rank_fusion(
            results_by_layer,
            plan.weights
        )
        # Apply preference boost for key SOP books when available
        fused_results = self._apply_sop_book_boost(plan.query_type, fused_results)

        # Final reranking
        final_results = self.simple_reranker(
            query,
            fused_results,
            plan.rerank_top_k
        )

        # Apply cross-encoder reranking if available (for even better relevance)
        if rerank_function and final_results:
            # Convert SearchResult objects to dicts for reranking
            results_as_dicts = [
                {
                    "id": r.id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in final_results
            ]

            # Rerank and convert back
            reranked_dicts = rerank_function(query, results_as_dicts, min(5, len(final_results)))

            final_results = [
                SearchResult(
                    id=r.get("id", ""),
                    osis_id=r.get("metadata", {}).get("osis_id"),
                    content=r.get("content", ""),
                    score=r.get("rerank_score", r.get("score", 0.0)),
                    source_layer=final_results[i].source_layer if i < len(final_results) else "",
                    metadata=r.get("metadata", {})
                )
                for i, r in enumerate(reranked_dicts)
            ]

        return final_results

    def _apply_sop_book_boost(self, query_type: QueryType, results: List[SearchResult]) -> List[SearchResult]:
        """Boost Conflict of the Ages series and Steps to Christ within SOP results.

        Applies a modest additive boost to fused scores for preferred books so they surface more often,
        without drowning out strong Bible results.
        """
        if not results:
            return results

        # Only boost for doctrinal or explicit SOP queries
        if query_type not in (QueryType.DOCTRINAL, QueryType.SOP_SPECIFIC):
            return results

        preferred_keywords = (
            'patriarchs and prophets',
            'prophets and kings',
            'desire of ages',
            'acts of the apostles',
            'great controversy',
            'steps to christ',
        )

        for r in results:
            try:
                if r.source_layer != 'sop':
                    continue
                book = ''
                if isinstance(r.metadata, dict):
                    book = (r.metadata.get('book') or '').strip()
                book_lc = book.lower()
                if any(k in book_lc for k in preferred_keywords):
                    # Add a small boost; keep it conservative
                    r.score += 0.15
            except Exception:
                # Best-effort only
                continue
        return results


def test_retrieval_router():
    """Test the retrieval router with sample queries"""
    router = RetrievalRouter()
    
    test_queries = [
        "John 3:16",
        "What is the unpardonable sin?",
        "According to Ellen White, what is salvation?",
        "Compare Romans 3:23 and John 3:16",
        "Sabbath observance"
    ]
    
    for query in test_queries:
        query_type = router.classify_query(query)
        plan = router.create_retrieval_plan(query)
        
        print(f"\nQuery: '{query}'")
        print(f"Type: {query_type.value}")
        print(f"Layers: {plan.layers}")
        print(f"K values: {plan.k_values}")
        print(f"Weights: {plan.weights}")


if __name__ == "__main__":
    test_retrieval_router()
