from __future__ import annotations

from typing import Dict, Tuple, Optional
import yaml
from pathlib import Path

from .config import OSIS_CONFIG_PATH


class OsisHelper:
    """Parses textual references into OSIS ids using alias mapping."""

    def __init__(self, path: Path | None = None):
        self.path: Path = path or OSIS_CONFIG_PATH
        with self.path.open() as f:
            self.cfg = yaml.safe_load(f)
        self.aliases: Dict[str, str] = {k.lower(): v for k, v in (self.cfg.get("book_aliases") or {}).items()}

    @staticmethod
    def _pad(ch: int, v: int) -> Tuple[str, str]:
        return f"{ch:02d}", f"{v:03d}"

    def normalize_book(self, name: str) -> Optional[str]:
        if not name:
            return None
        n = name.strip()
        if n in self.aliases.values():
            return n
        return self.aliases.get(n.lower()) or n

    def to_osis(self, text: str) -> Optional[str]:
        if not text:
            return None
        t = text.strip().replace("&", "")
        import re
        t = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", t)
        t = re.sub(r"\s+", " ", t).strip()
        m = re.match(r"^(\d+\s+)?([A-Za-z.]+)\s+(\d+):(\d+)$", t)
        if not m:
            return None
        book_num, book_name, ch, vs = m.groups()
        book = f"{(book_num or '').strip()} {book_name}".strip()
        book = self.normalize_book(book)
        if not book:
            return None
        chp, vsp = self._pad(int(ch), int(vs))
        return f"{book}.{chp}.{vsp}"

