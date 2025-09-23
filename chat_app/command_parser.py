from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParsedCommand:
    kind: str  # 'at', 'amp', 'hash', 'slash', 'text'
    value: str


def parse_command(line: str) -> ParsedCommand:
    s = (line or "").strip()
    if not s:
        return ParsedCommand(kind="text", value="")
    if s.startswith("/"):
        return ParsedCommand(kind="slash", value=s[1:].strip())
    if s.startswith("!"):
        return ParsedCommand(kind="bang", value=s[1:].strip())
    if s.startswith("@"):
        return ParsedCommand(kind="at", value=s[1:].strip())
    if s.startswith("&"):
        return ParsedCommand(kind="amp", value=s[1:].strip())
    if s.startswith("#"):
        return ParsedCommand(kind="hash", value=s[1:].strip())
    return ParsedCommand(kind="text", value=s)
