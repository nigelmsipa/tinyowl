from __future__ import annotations

from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


def print_header(title: str) -> None:
    console.print(Panel.fit(Text(title, style="bold cyan")))


def print_suggestions(items: List[Dict[str, Any]]) -> None:
    table = Table(title="Suggestions", header_style="bold magenta")
    table.add_column("Term", style="cyan", no_wrap=True)
    table.add_column("Count", style="green", no_wrap=True)
    for it in items:
        table.add_row(it["term"], str(it["count"]))
    console.print(table)


def print_verse_results(results: List[Dict[str, Any]]) -> None:
    table = Table(title="Scripture References", header_style="bold magenta")
    table.add_column("Source", style="yellow", no_wrap=True)
    table.add_column("OSIS", style="cyan", no_wrap=True)
    table.add_column("Text", style="white")
    for r in results:
        table.add_row(r.get("source", ""), r.get("osis_id", ""), r.get("text", ""))
    console.print(table)


def print_concordance_results(word: str, items: List[Dict[str, Any]], show: int = 5) -> None:
    title = f"Occurrences for @{word} (showing {min(show, len(items))} of {len(items)})"
    console.print(Panel.fit(title, title="Concordance", style="bold blue"))
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("OSIS", style="cyan", no_wrap=True)
    table.add_column("Excerpt", style="white")
    for item in items[:show]:
        osis_id = (item.get("metadata") or {}).get("osis_id") or ""
        excerpt = item.get("content", "")
        table.add_row(osis_id, excerpt)
    console.print(table)
    if len(items) > show:
        console.print("[dim]Type 'more' to show additional results[/dim]")


def print_router_results(q: str, items: List[Dict[str, Any]], show: int = 5) -> None:
    title = f"Topical Search: '{q}' (showing {min(show, len(items))} of {len(items)})"
    console.print(Panel.fit(title, title="Search", style="bold green"))
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Score", style="green", no_wrap=True)
    table.add_column("Layer", style="yellow", no_wrap=True)
    table.add_column("OSIS", style="cyan", no_wrap=True)
    table.add_column("Excerpt", style="white")
    for r in items[:show]:
        table.add_row(f"{r.get('score', 0):.3f}", r.get("source_layer", ""), r.get("osis_id") or "", (r.get("content") or "")[:140] + "…")
    console.print(table)


def print_info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")


def print_error(msg: str) -> None:
    console.print(Panel.fit(Text(msg, style="bold red"), title="Error"))


def print_keyword_results(term: str, items: List[Dict[str, Any]], show: int = 10) -> None:
    title = f"Keyword search: '{term}' (showing {min(show, len(items))} of {len(items)})"
    console.print(Panel.fit(title, title="Keyword", style="bold cyan"))
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("OSIS", style="cyan", no_wrap=True)
    table.add_column("Src", style="yellow", no_wrap=True)
    table.add_column("Text", style="white")
    for r in items[:show]:
        table.add_row(r.get("osis_id", ""), r.get("source", ""), r.get("text", ""))
    console.print(table)
    if len(items) > show:
        console.print("[dim]Type 'more' to show additional results[/dim]")


def print_strongs_root(word: str, entries: List[Dict[str, Any]]) -> None:
    """Show Strong's root word summary for a keyword.

    entries: list of {number, snippet}
    """
    title = f"Strong's Root for '{word}'"
    console.print(Panel.fit(title, title="Root", style="bold blue"))
    if not entries:
        console.print("[dim]No Strong's entries found[/dim]")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Strong#", style="yellow", no_wrap=True)
    table.add_column("Lang", style="cyan", no_wrap=True)
    table.add_column("Lemma", style="green", no_wrap=True)
    table.add_column("Translit", style="magenta", no_wrap=True)
    table.add_column("Definition", style="white")
    for e in entries[:5]:
        table.add_row(
            e.get("number", ""),
            e.get("language", ""),
            e.get("lemma", ""),
            e.get("transliteration", ""),
            e.get("definition", ""),
        )
    console.print(table)
