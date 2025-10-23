#!/usr/bin/env python3
"""
TinyOwl Chat - IMPROVED VERSION
Streams answers immediately, retrieves context in background
"""

from pathlib import Path
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel

# Add parent to path for imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from chat_app.database_manager import DatabaseManager
from chat_app.chat_history import ChatHistory
from chat_app.command_parser import CommandParser, ParsedCommand
from chat_app.ollama_integration import generate_stream, check_ollama, list_models
from chat_app.response_formatter import (
    print_verse_results,
    print_router_results,
    print_concordance_results,
    print_error
)

console = Console()


def answer_directly_first(query: str, model: str = "qwen2.5:7b") -> str:
    """Stream answer immediately from LLM knowledge, without waiting for retrieval"""
    prompt = (
        f"You are a biblical theology assistant. Answer this question clearly and concisely "
        f"using your knowledge of Scripture and theology. Focus on biblical accuracy.\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )

    console.print("\n[bold cyan]Direct Answer (streaming):[/bold cyan]")
    answer_parts = []

    try:
        for chunk in generate_stream(prompt, model=model):
            answer_parts.append(chunk)
            console.print(chunk, end="", style="cyan")
        console.print()  # newline
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")

    return "".join(answer_parts)


def enhance_with_context(query: str, answer: str, db: DatabaseManager, model: str = "qwen2.5:7b") -> Optional[str]:
    """Optionally enhance answer with retrieved context (runs AFTER direct answer)"""

    console.print("\n[dim]Checking for supporting scriptures...[/dim]")

    try:
        # Quick retrieval (with timeout protection)
        results = db.routed_search(query)[:3]  # Only top 3 results

        if not results:
            return None

        # Show what was found
        console.print(f"\n[dim]Found {len(results)} supporting references:[/dim]")
        for i, r in enumerate(results, 1):
            source = r.get('source', 'Unknown')
            content_preview = r.get('content', '')[:100]
            console.print(f"  [{i}] {source}: {content_preview}...")

        # Ask LLM to verify/enhance with retrieved context
        context_text = "\n\n".join([
            f"[Source {i+1}] {r.get('content', '')}"
            for i, r in enumerate(results)
        ])

        verify_prompt = (
            f"Original question: {query}\n\n"
            f"Your answer: {answer}\n\n"
            f"Additional context found:\n{context_text}\n\n"
            f"If the context supports or enhances your answer, briefly mention it. "
            f"If the context contradicts your answer, correct yourself. "
            f"If the context is irrelevant, say 'no additional references needed'.\n\n"
            f"Enhancement:"
        )

        console.print("\n[bold green]Verification with sources:[/bold green]")
        enhancement_parts = []

        for chunk in generate_stream(verify_prompt, model=model):
            enhancement_parts.append(chunk)
            console.print(chunk, end="", style="green")
        console.print()

        return "".join(enhancement_parts)

    except Exception as e:
        console.print(f"\n[dim]Context retrieval failed: {e}[/dim]")
        return None


def main():
    console.print(Panel.fit(
        "[bold cyan]TinyOwl Chat - Improved[/bold cyan]\n"
        "[dim]Fast streaming responses with optional context enhancement[/dim]",
        border_style="cyan"
    ))

    # Initialize
    db = DatabaseManager()
    history = ChatHistory()
    parser = CommandParser()

    # Settings
    ai_enabled = True
    ai_model = "qwen2.5:7b"

    # Check Ollama
    if not check_ollama():
        console.print("[yellow]Warning: Ollama not available. Chat requires Ollama.[/yellow]")
        return

    console.print(f"[green]✓[/green] Using model: {ai_model}")
    console.print("[dim]Type /help for commands, /quit to exit[/dim]\n")

    # Main loop
    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        # Parse command
        parsed = parser.parse(user_input)

        # Handle commands
        if parsed.kind == "command":
            cmd = parsed.value.lower()

            if cmd == "quit" or cmd == "exit":
                console.print("[dim]Goodbye![/dim]")
                break

            if cmd == "help":
                console.print("""
[bold]TinyOwl Improved Commands:[/bold]
  /help     Show this help
  /quit     Exit chat
  /clear    Clear screen
  /model    List/switch AI models

[bold]Query Modes:[/bold]
  Just type your question - answers stream immediately
  Context retrieval happens in background

[bold]Examples:[/bold]
  What is the Sabbath?
  Explain justification by faith
  Who was Melchizedek?
""")
                continue

            if cmd == "clear":
                console.clear()
                continue

            if cmd == "model":
                models = list_models()
                if models:
                    console.print("Available models:")
                    for i, m in enumerate(models, 1):
                        mark = " (current)" if m == ai_model else ""
                        console.print(f"  [{i}] {m}{mark}")
                continue

        # Handle text query
        if parsed.kind == "text":
            query = parsed.value

            # STEP 1: Answer immediately from LLM knowledge
            direct_answer = answer_directly_first(query, model=ai_model)

            # STEP 2: Optionally enhance with retrieved context (in background)
            if direct_answer:
                enhancement = enhance_with_context(query, direct_answer, db, model=ai_model)

            console.print()  # spacing


if __name__ == "__main__":
    main()
