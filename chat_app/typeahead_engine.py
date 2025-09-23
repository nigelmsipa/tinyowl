from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import json
from pathlib import Path

from .config import STRONGS_CONCORDANCE_JSON


@dataclass
class Suggestion:
    term: str
    count: int


class TypeaheadEngine:
    """Loads Strong's concordance word index and provides fast suggestions."""

    def __init__(self, path: Path | None = None):
        self.path: Path = path or STRONGS_CONCORDANCE_JSON
        self._counts: Dict[str, int] = {}
        self._index: Dict[str, List[Dict]] = {}
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        if self._loaded:
            return
        with self.path.open() as f:
            data = json.load(f)
        for item in data:
            meta = item.get("metadata", {})
            word = meta.get("word", "").lower()
            if not word:
                continue
            self._counts[word] = self._counts.get(word, 0) + 1
            self._index.setdefault(word, []).append(item)
        self._loaded = True

    def suggest(self, prefix: str, limit: int = 10) -> List[Suggestion]:
        if not self._loaded:
            self.load()
        p = prefix.lower()
        starts = [(w, c) for w, c in self._counts.items() if w.startswith(p)]
        contains = [(w, c) for w, c in self._counts.items() if p in w and not w.startswith(p)]
        starts.sort(key=lambda t: (-t[1], t[0]))
        contains.sort(key=lambda t: (-t[1], t[0]))
        merged = starts + contains
        return [Suggestion(term=w, count=c) for w, c in merged[:limit]]

    def occurrences(self, term: str, limit: int = 50) -> List[Dict]:
        if not self._loaded:
            self.load()
        items = self._index.get(term.lower(), [])
        return items[:limit]

