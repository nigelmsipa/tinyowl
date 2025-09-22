#!/usr/bin/env python3
from __future__ import annotations

import os
import json
import time
from typing import Dict, Any, Optional

import readline  # Provides history + tab completion
from rich.console import Console
import sys
try:
    import curses  # for arrow-key interactive selection
except Exception:  # pragma: no cover
    curses = None  # type: ignore

from .config import APP_DATA_DIR, HISTORY_FILE_PATH, DEFAULT_AI_MODEL, OLLAMA_HOST
from .settings import load_settings, save_settings
from .typeahead_engine import TypeaheadEngine
from .database_manager import DatabaseManager
from .response_formatter import (
    print_suggestions,
    print_verse_results,
    print_concordance_results,
    print_router_results,
    print_keyword_results,
    print_error,
)
from .command_parser import parse_command
from .chat_history import ChatHistory
from .ollama_integration import check_ollama, enhance_with_ai, list_models, generate_stream
from .osis import OsisHelper


console = Console()


class Completer:
    def __init__(self, typeahead: TypeaheadEngine):
        self.typeahead = typeahead
        self.current_suggestions = []

    def complete(self, text: str, state: int):
        buffer = readline.get_line_buffer()
        if buffer.startswith("@"):  # Strong's words
            prefix = buffer[1:]
            sugs = self.typeahead.suggest(prefix, limit=10)
            self.current_suggestions = [f"@{s.term}" for s in sugs]
        elif buffer.startswith("/"):
            cmds = [
                "/help", "/history", "/export", "/clear", "/stats",
                "/ai status", "/ai on", "/ai off", "/ai toggle", "/ai models",
                "/ai model", "/ai help", "/ai default", "/model",
            ]
            self.current_suggestions = [c for c in cmds if c.startswith(buffer)]
        else:
            self.current_suggestions = []

        try:
            return self.current_suggestions[state]
        except IndexError:
            return None


def ensure_dirs() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE_PATH.touch(exist_ok=True)


def interactive_model_picker(models: list[str], current: Optional[str] = None) -> Optional[str]:
    """Interactive arrow-key picker using curses. Returns selected model, or None if cancelled.

    Falls back to None if curses or TTY is unavailable.
    """
    if not models:
        return None
    if curses is None or not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    def _ui(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)
        sel = 0
        if current and current in models:
            sel = models.index(current)
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Select Ollama Model (↑/↓, Enter=confirm, Esc=cancel)"
            stdscr.addnstr(0, 0, title, w - 1, curses.A_BOLD)
            for i, m in enumerate(models):
                marker = "→ " if i == sel else "  "
                suffix = "  (current)" if current and m == current else ""
                line = f"{marker}{m}{suffix}"
                attr = curses.A_REVERSE if i == sel else curses.A_NORMAL
                if 1 + i < h - 1:
                    stdscr.addnstr(1 + i, 0, line, w - 1, attr)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (curses.KEY_UP, ord('k')):
                sel = (sel - 1) % len(models)
            elif ch in (curses.KEY_DOWN, ord('j')):
                sel = (sel + 1) % len(models)
            elif ch in (curses.KEY_ENTER, 10, 13):
                return models[sel]
            elif ch in (27, ord('q')):
                return None

    try:
        return curses.wrapper(_ui)
    except Exception:
        return None


def main() -> None:
    ensure_dirs()

    try:
        readline.read_history_file(HISTORY_FILE_PATH)
    except FileNotFoundError:
        pass

    typeahead = TypeaheadEngine()
    db = DatabaseManager()
    start_load = time.perf_counter()
    with console.status("Initializing lookup indexes…", spinner="dots"):
        db.load_fast_lookup()
    console.print(f"[dim]Ready in {(time.perf_counter()-start_load)*1000:.0f} ms[/dim]")
    osis = OsisHelper()
    history = ChatHistory()

    settings = load_settings()
    # Default to saved settings; if none, start with Ollama availability and default model
    ai_enabled = settings.get("default_ai_enabled", check_ollama())
    ai_model = settings.get("default_ai_model", DEFAULT_AI_MODEL)
    session_id = history.create_session(ai_enabled=ai_enabled, ai_model=ai_model)

    comp = Completer(typeahead)
    readline.set_completer(comp.complete)
    readline.parse_and_bind("tab: complete")

    console.print("TinyOwl Chat (CLI)")
    console.print("Type '/help' for commands. 'Ctrl+C' to exit.")
    console.print(f"AI enhancement: {'ON' if ai_enabled else 'OFF'} (model: {ai_model})")
    console.print(f"Ollama: {'YES' if check_ollama() else 'NO'} at {OLLAMA_HOST}")

    last_results_cache: Dict[str, Any] = {}

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break

        if not line:
            continue

        parsed = parse_command(line)

        if parsed.kind == "slash":
            cmd = parsed.value
            if cmd in ("help",):
                console.print(
                    "Commands: /help, /history, /export, /clear, /stats, /ai on|off|toggle|status|models|model <name>|default|help, /model"
                )
                continue
            # Short alias for model switching: `/model` acts like `/ai model`
            if cmd == "model" or cmd.startswith("model "):
                cmd = "ai model" + (" " + cmd[len("model"):].strip() if len(cmd) > len("model") else "")
            if cmd.startswith("ai"):
                sub = cmd.split()
                action = sub[1] if len(sub) > 1 else "status"
                if action == "help":
                    console.print(
                        """
/ai help            Show this help
/ai status          Show AI toggle, Ollama availability, and current model
/ai on|off|toggle   Control AI enhancement
/ai models          List installed models (numbered; marks current)
/ai model <name>    Switch model (name, number, or partial)
/ai model           Pick interactively (enter number or name)
/ai default [name]  Save defaults for future sessions (current or given name)
                        """.strip()
                    )
                    continue
                if action == "toggle":
                    ai_enabled = not ai_enabled
                    history.update_session_ai_enabled(session_id, ai_enabled)
                    console.print(f"AI enhancement: {'ON' if ai_enabled else 'OFF'} (model: {ai_model})")
                    continue
                if action == "on":
                    ai_enabled = True
                    history.update_session_ai_enabled(session_id, True)
                    console.print(f"AI enhancement: ON (model: {ai_model})")
                    continue
                if action == "off":
                    ai_enabled = False
                    history.update_session_ai_enabled(session_id, False)
                    console.print("AI enhancement: OFF")
                    continue
                if action == "status":
                    available = check_ollama()
                    console.print(
                        f"AI enhancement: {'ON' if ai_enabled else 'OFF'} | Ollama available: {'YES' if available else 'NO'} | model: {ai_model}"
                    )
                    continue
                if action == "models":
                    with console.status("Querying Ollama for models…", spinner="dots"):
                        models = list_models()
                    if not models:
                        console.print("No models found or Ollama unavailable.")
                    else:
                        lines = [f"[{i+1}] {m}{'  (current)' if m == ai_model else ''}" for i, m in enumerate(models)]
                        console.print("Available models:\n" + "\n".join(lines))
                    continue
                if action == "model":
                    models = list_models()
                    if not models:
                        console.print("No models found or Ollama unavailable.")
                        continue
                    # If no argument, try interactive picker first
                    if len(sub) < 3:
                        choice = interactive_model_picker(models, current=ai_model)
                        if not choice:
                            lines = [f"[{i+1}] {m}{'  (current)' if m == ai_model else ''}" for i, m in enumerate(models)]
                            console.print("Select a model by number or name:\n" + "\n".join(lines))
                            try:
                                choice = input("Model > ").strip()
                            except (EOFError, KeyboardInterrupt):
                                console.print("\n[dim]Cancelled[/dim]")
                                continue
                    else:
                        choice = " ".join(sub[2:]).strip()

                    # Allow numeric index
                    new_model = None
                    if choice and choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(models):
                            new_model = models[idx]
                    # Try exact match
                    if new_model is None and choice in models:
                        new_model = choice
                    # Fuzzy: case-insensitive substring, prefer unique
                    if new_model is None and choice:
                        matches = [m for m in models if choice.lower() in m.lower()]
                        if len(matches) == 1:
                            new_model = matches[0]
                        elif len(matches) > 1:
                            console.print("Ambiguous model name. Matches:\n- " + "\n- ".join(matches))
                            continue
                    if not new_model:
                        console.print("Model not found.")
                        continue
                    ai_model = new_model
                    history.update_session_ai_model(session_id, ai_model)
                    console.print(f"AI model set to: {ai_model}")
                    continue
                if action == "default":
                    # Persist current or provided model and enabled flag for future sessions
                    desired = ai_model
                    if len(sub) >= 3:
                        desired = " ".join(sub[2:]).strip()
                    # Save without strict validation to allow setting before pulling
                    settings["default_ai_model"] = desired
                    settings["default_ai_enabled"] = ai_enabled
                    save_settings(settings)
                    console.print(f"Saved defaults: model={desired}, enabled={'ON' if ai_enabled else 'OFF'}")
                    continue
                console.print("Unknown /ai subcommand. Try /ai status")
                continue
            if cmd == "history":
                sessions = history.recent_sessions(limit=10)
                for sid, created, ai in sessions:
                    console.print(f"Session {sid} — {created} — AI={'ON' if ai else 'OFF'}")
                continue
            if cmd.startswith("export"):
                from .config import EXPORTS_DIR
                EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
                msgs = history.get_session_messages(session_id)
                out = []
                for role, content, ts in msgs:
                    out.append({"role": role, "content": content, "time": ts})
                path = EXPORTS_DIR / f"session_{session_id}.json"
                path.write_text(json.dumps(out, indent=2))
                console.print(f"Exported to {path}")
                continue
            if cmd == "clear":
                os.system("clear")
                continue
            if cmd == "stats":
                st = db.stats()
                console.print(json.dumps(st, indent=2))
                continue
            console.print("Unknown command. Try /help")
            continue

        if parsed.kind == "at":
            val = parsed.value
            # Strong's number lookup: @strong:175 or @H175/@G3056
            if val.lower().startswith("strong:") or val.upper().startswith(("H", "G")):
                num = val.split(":", 1)[1] if ":" in val else val
                item = db.strongs_lookup(num)
                if not item:
                    print_error("No Strong's entry found.")
                    continue
                console.print("")
                console.rule(f"Strong's {item['metadata'].get('strong_number')}")
                console.print(item.get("content", "(no content)"))
                history.add_message(session_id, "user", f"@strong:{num}")
                continue

            word = val
            if not typeahead.loaded:
                with console.status("Loading concordance index…", spinner="dots"):
                    typeahead.load()
            sugs = typeahead.suggest(word, limit=10)
            print_suggestions([{"term": s.term, "count": s.count} for s in sugs])
            with console.status("Scanning occurrences…", spinner="dots"):
                occ = typeahead.occurrences(word, limit=100)
            print_concordance_results(word, occ, show=5)
            last_results_cache = {"kind": "concordance", "word": word, "items": occ, "shown": 5}
            history.add_message(session_id, "user", f"@{word}")
            continue

        # '!' keyword lexical search across KJV/WEB verses
        if parsed.kind == "bang":
            term = parsed.value
            with console.status("Keyword search…", spinner="dots"):
                items = db.lexical_search(term)
            print_keyword_results(term, items, show=10)
            last_results_cache = {"kind": "lexical", "term": term, "items": items, "shown": 10}
            history.add_message(session_id, "user", f"!{term}")
            continue

        if parsed.kind == "amp":
            ref = parsed.value
            osid = osis.to_osis(ref)
            if not osid:
                print_error("Could not parse verse reference. Try 'John 3:16'.")
                continue
            with console.status("Retrieving verses…", spinner="dots"):
                verses = db.verse_lookup(osid)
            if not verses:
                print_error(f"No verse found for {osid}")
                continue
            print_verse_results([
                {"source": v.source, "osis_id": v.osis_id, "text": v.text} for v in verses
            ])
            history.add_message(session_id, "user", f"&{ref}")
            continue

        if parsed.kind == "hash":
            q = parsed.value
            with console.status("Searching across sources…", spinner="dots"):
                results = db.routed_search(q)
            print_router_results(q, results, show=5)
            history.add_message(session_id, "user", f"#{q}")
            if ai_enabled and check_ollama():
                ctx = "\n\n".join([f"[{i+1}] {r.get('content','')}" for i, r in enumerate(results[:5])])
                prompt = (
                    "You are a theological research assistant. Using ONLY the context provided, answer the query and cite sources by [index].\n\n"
                    f"Context:\n{ctx}\n\nQuery: {q}\nAnswer:"
                )
                console.print("\n[bold green]AI-enhanced summary (streaming):[/bold green]")
                ai_text = []
                it = generate_stream(prompt, model=ai_model)
                first_chunk: Optional[str] = None
                # Show spinner until first token arrives
                with console.status(f"AI ({ai_model}) composing…", spinner="dots"):
                    try:
                        first_chunk = next(it)
                    except StopIteration:
                        first_chunk = None
                    except KeyboardInterrupt:
                        console.print("\n[dim]AI streaming interrupted by user[/dim]")
                        first_chunk = None
                if first_chunk:
                    ai_text.append(first_chunk)
                    console.print(first_chunk, end="")
                try:
                    for chunk in it:
                        ai_text.append(chunk)
                        console.print(chunk, end="")
                    console.print("")
                except KeyboardInterrupt:
                    console.print("\n[dim]AI streaming interrupted by user[/dim]")
                full = "".join(ai_text).strip()
                if full:
                    history.add_message(session_id, "assistant", full)
            continue

        if parsed.kind == "text":
            # Special: paginate concordance results when user types 'more'
            if parsed.value.lower() == "more":
                if last_results_cache.get("kind") == "concordance":
                    items = last_results_cache.get("items", [])
                    shown = last_results_cache.get("shown", 0)
                    show_next = min(shown + 5, len(items))
                    print_concordance_results(last_results_cache.get("word", ""), items, show=show_next)
                    last_results_cache["shown"] = show_next
                    continue
                if last_results_cache.get("kind") == "lexical":
                    items = last_results_cache.get("items", [])
                    shown = last_results_cache.get("shown", 0)
                    show_next = min(shown + 10, len(items))
                    print_keyword_results(last_results_cache.get("term", ""), items, show=show_next)
                    last_results_cache["shown"] = show_next
                    continue

            q = parsed.value
            with console.status("Searching across sources…", spinner="dots"):
                results = db.routed_search(q)
            print_router_results(q, results, show=5)
            history.add_message(session_id, "user", q)
            if ai_enabled and check_ollama():
                ctx = "\n\n".join([f"[{i+1}] {r.get('content','')}" for i, r in enumerate(results[:5])])
                prompt = (
                    "You are a theological research assistant. Using ONLY the context provided, answer the query and cite sources by [index].\n\n"
                    f"Context:\n{ctx}\n\nQuery: {q}\nAnswer:"
                )
                console.print("\n[bold green]AI-enhanced summary (streaming):[/bold green]")
                ai_text = []
                it = generate_stream(prompt, model=ai_model)
                first_chunk: Optional[str] = None
                with console.status(f"AI ({ai_model}) composing…", spinner="dots"):
                    try:
                        first_chunk = next(it)
                    except StopIteration:
                        first_chunk = None
                    except KeyboardInterrupt:
                        console.print("\n[dim]AI streaming interrupted by user[/dim]")
                        first_chunk = None
                if first_chunk:
                    ai_text.append(first_chunk)
                    console.print(first_chunk, end="")
                try:
                    for chunk in it:
                        ai_text.append(chunk)
                        console.print(chunk, end="")
                    console.print("")
                except KeyboardInterrupt:
                    console.print("\n[dim]AI streaming interrupted by user[/dim]")
                full = "".join(ai_text).strip()
                if full:
                    history.add_message(session_id, "assistant", full)
            continue


if __name__ == "__main__":
    main()
