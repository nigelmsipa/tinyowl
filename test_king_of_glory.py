#!/usr/bin/env python3
"""Test the enhanced search for 'King of Glory' query"""

import sys
from pathlib import Path

# Add chat_app to path
sys.path.insert(0, str(Path(__file__).parent / "chat_app"))

from database_manager import DatabaseManager
from rich.console import Console
from rich.table import Table

console = Console()

def test_king_of_glory():
    """Test the King of Glory query with new enhancements"""

    console.print("\n[bold cyan]Testing Enhanced Search Pipeline[/bold cyan]")
    console.print("Query: 'who is the King of Glory?'\n")

    # Initialize database
    db = DatabaseManager()
    console.print("[dim]Loading database...[/dim]")
    db.load_fast_lookup()

    # Test query
    query = "who is the King of Glory?"

    console.print("\n[bold green]1. Running enhanced routed search (with reranking)...[/bold green]")
    results = db.routed_search(query, use_reranking=True)

    # Display results
    if results:
        table = Table(title="Enhanced Search Results")
        table.add_column("Score", style="cyan", width=8)
        table.add_column("OSIS", style="magenta", width=15)
        table.add_column("Content", style="white", width=60)

        for i, r in enumerate(results[:5], 1):
            osis = r.get("osis_id", "N/A")
            content = r.get("content", "")[:100] + "..." if len(r.get("content", "")) > 100 else r.get("content", "")
            score = f"{r.get('score', 0):.3f}"
            table.add_row(score, osis, content)

        console.print(table)

        # Show the top result in detail
        if results[0].get("osis_id"):
            console.print(f"\n[bold yellow]Top Result Details:[/bold yellow]")
            console.print(f"OSIS ID: {results[0]['osis_id']}")
            console.print(f"Score: {results[0].get('score', 0):.4f}")
            console.print(f"Content:\n{results[0].get('content', '')}")

    else:
        console.print("[red]No results found![/red]")

    console.print("\n[bold green]2. Testing without reranking (faster but less accurate)...[/bold green]")
    results_no_rerank = db.routed_search(query, use_reranking=False)
    console.print(f"Results: {len(results_no_rerank)} found")
    if results_no_rerank:
        console.print(f"Top result: {results_no_rerank[0].get('osis_id', 'N/A')}")

    console.print("\n[bold cyan]Test Complete![/bold cyan]")
    console.print(f"Expected: Psalm 24:7-10 (King of Glory passage)")
    if results and 'Ps' in str(results[0].get('osis_id', '')):
        console.print("[green]✓ SUCCESS: Found Psalm reference![/green]")
    else:
        console.print("[yellow]⚠ Check: Top result might not be ideal[/yellow]")

if __name__ == "__main__":
    test_king_of_glory()
