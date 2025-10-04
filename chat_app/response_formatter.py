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


def print_semantic_similarity(word: str, similar_words: List[Dict[str, Any]]) -> None:
    """Display semantically similar words ranked by vector similarity.

    similar_words: list of {word, similarity}
    """
    title = f"Words semantically similar to '{word}'"
    console.print(Panel.fit(title, title="Semantic Similarity", style="bold magenta"))

    if not similar_words:
        console.print("[dim]No similar words found[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Word", style="cyan", no_wrap=False)
    table.add_column("Similarity", style="green", no_wrap=True)

    for idx, item in enumerate(similar_words, 1):
        table.add_row(
            str(idx),
            item.get("word", ""),
            f"{item.get('similarity', 0):.3f}"
        )

    console.print(table)
    console.print("\n[dim]💡 Tip: Use @word for concordance or #word for topical search[/dim]")


def print_concept_similarity(expression: str, payload: Dict[str, Any]) -> None:
    """Display concept-vector neighbours with seed word details."""
    title = f"Concept vector for '{expression}'"
    console.print(Panel.fit(title, title="Concept Vector", style="bold magenta"))

    positives = [w.lower() for w in payload.get("positives", []) if w]
    negatives = [w.lower() for w in payload.get("negatives", []) if w]
    results = payload.get("results", [])

    if positives:
        console.print(f"[cyan]Positive seeds:[/cyan] {', '.join(positives)}")
    if negatives:
        console.print(f"[cyan]Negative seeds:[/cyan] {', '.join(negatives)}")

    if not results:
        console.print("[dim]No neighbouring words found[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Word", style="cyan", no_wrap=False)
    table.add_column("Similarity", style="green", no_wrap=True)

    for idx, item in enumerate(results, 1):
        table.add_row(
            str(idx),
            item.get("word", ""),
            f"{item.get('similarity', 0):.3f}"
        )

    console.print(table)
    console.print("\n[dim]💡 Tip: Mix positives and negatives, e.g., ~concept love+mercy-judgment[/dim]")


def print_analogy_results(expression: str, payload: Dict[str, Any]) -> None:
    """Present analogy-style vector results."""
    title = f"Analogy vector for '{expression}'"
    console.print(Panel.fit(title, title="Analogy", style="bold magenta"))

    positives = [w.lower() for w in payload.get("positives", []) if w]
    negatives = [w.lower() for w in payload.get("negatives", []) if w]
    results = payload.get("results", [])

    if positives:
        console.print(f"[cyan]Add:[/cyan] {', '.join(positives)}")
    if negatives:
        console.print(f"[cyan]Subtract:[/cyan] {', '.join(negatives)}")

    if not results:
        console.print("[dim]No candidate words found[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Candidate", style="cyan", no_wrap=False)
    table.add_column("Similarity", style="green", no_wrap=True)

    for idx, item in enumerate(results, 1):
        table.add_row(str(idx), item.get("word", ""), f"{item.get('similarity', 0):.3f}")

    console.print(table)
    console.print("\n[dim]💡 Tip: Try patterns like king-man+woman or faith-grace+obedience[/dim]")
