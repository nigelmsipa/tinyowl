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
    print_strongs_root,
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
                "/mode", "/mode status", "/mode help", "/mode default",
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


def interactive_mode_picker(modes: list[str], current: Optional[str] = None) -> Optional[str]:
    """Interactive arrow-key picker for modes. Returns selected mode or None.

    Falls back to None if curses or TTY is unavailable.
    """
    if not modes:
        return None
    if curses is None or not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    def _ui(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)
        sel = 0
        if current and current in modes:
            sel = modes.index(current)
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Select Mode (↑/↓, Enter=confirm, Esc=cancel)"
            stdscr.addnstr(0, 0, title, w - 1, curses.A_BOLD)
            for i, m in enumerate(modes):
                marker = "→ " if i == sel else "  "
                suffix = "  (current)" if current and m == current else ""
                line = f"{marker}{m.title()}{suffix}"
                attr = curses.A_REVERSE if i == sel else curses.A_NORMAL
                if 1 + i < h - 1:
                    stdscr.addnstr(1 + i, 0, line, w - 1, attr)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (curses.KEY_UP, ord('k')):
                sel = (sel - 1) % len(modes)
            elif ch in (curses.KEY_DOWN, ord('j')):
                sel = (sel + 1) % len(modes)
            elif ch in (curses.KEY_ENTER, 10, 13):
                return modes[sel]
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
    # Modes: natural (default), topic, verses, concordance, keyword
    mode: str = settings.get("default_mode", "natural").lower()
    valid_modes = ["natural", "topic", "verses", "concordance", "keyword"]
    if mode not in valid_modes:
        mode = "natural"
    session_id = history.create_session(ai_enabled=ai_enabled, ai_model=ai_model)

    comp = Completer(typeahead)
    readline.set_completer(comp.complete)
    readline.parse_and_bind("tab: complete")

    console.print("TinyOwl Chat (CLI)")
    console.print("Type '/help' for commands. 'Ctrl+C' to exit.")
    def mode_label(m: str) -> str:
        labels = {
            "natural": "Natural",
            "topic": "Topic",
            "verses": "Verses",
            "concordance": "Concordance",
            "keyword": "Keyword",
        }
        return labels.get(m, m)

    def mode_abbrev(m: str) -> str:
        return {
            "natural": "Nat",
            "topic": "Top",
            "verses": "Ver",
            "concordance": "Con",
            "keyword": "Key",
        }.get(m, m[:3].title())

    def prompt_label(m: str) -> str:
        style = settings.get("prompt_style", "abbr").lower()  # abbr | emoji | none
        if style == "emoji":
            return "🦉"
        if style == "none":
            return ""
        # default: abbreviation per mode
        return mode_abbrev(m)

    def should_show_root_panel(query: str) -> bool:
        mode_setting = settings.get("root_display", "auto").lower()  # auto | always | off
        if mode_setting == "off":
            return False
        if mode_setting == "always":
            return True
        # auto heuristic: short, keyword-centric prompts, not commands
        s = (query or "").strip()
        if not s or s[0] in ("/", "@", "#", "&", "!"):
            return False
        toks = [t.strip(".,!?;:\"'()[]{}").lower() for t in s.split() if t.strip()]
        if len(toks) <= 1:
            return True
        if len(toks) <= 4 and ((toks[0] == "what" and len(toks) >= 2 and toks[1] in {"is","are","does"}) or toks[0] in {"define","explain","meaning"}):
            return True
        return False

    def show_status() -> None:
        console.print(
            f"[dim]Mode: {mode_label(mode)} | AI: {'ON' if ai_enabled else 'OFF'} | Model: {ai_model} | Ollama: {'YES' if check_ollama() else 'NO'} @ {OLLAMA_HOST}[/dim]"
        )
    show_status()

    last_results_cache: Dict[str, Any] = {}

    while True:
        try:
            label = prompt_label(mode)
            prefix = f"{label} > " if label else "> "
            line = input(f"\n{prefix}").strip()
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
                    "Commands: /help, /history, /export, /clear, /stats, /mode [name|help|status|default], /ai on|off|toggle|status|models|model <name>|default|help, /model, /prompt [emoji|abbr|none]"
                )
                continue
            # Short alias for model switching: `/model` acts like `/ai model`
            if cmd == "model" or cmd.startswith("model "):
                cmd = "ai model" + (" " + cmd[len("model"):].strip() if len(cmd) > len("model") else "")
            # Prompt style commands
            if cmd.startswith("prompt"):
                parts = cmd.split()
                current = settings.get("prompt_style", "abbr")
                if len(parts) == 1 or parts[1] in ("help", "status"):
                    console.print(f"[dim]Prompt style: {current} (options: emoji, abbr, none)[/dim]")
                    continue
                choice = parts[1].lower()
                if choice not in ("emoji", "abbr", "none"):
                    print_error("Invalid prompt style. Use: /prompt emoji|abbr|none")
                    continue
                settings["prompt_style"] = choice
                save_settings(settings)
                console.print(f"[dim]Prompt style saved: {choice}[/dim]")
                show_status()
                continue
            # Mode commands
            if cmd.startswith("mode"):
                parts = cmd.split()
                # If no sub-arg, open interactive picker instead of status
                if len(parts) == 1:
                    picked = interactive_mode_picker(valid_modes, current=mode)
                    if picked:
                        mode = picked
                        console.print(f"Mode set to: {mode_label(mode)}")
                        show_status()
                        continue
                    # Explain why picker didn't appear
                    try:
                        import sys as _sys
                        if curses is None:
                            console.print("[dim]Interactive picker unavailable: curses not available[/dim]")
                        elif not (_sys.stdin.isatty() and _sys.stdout.isatty()):
                            console.print("[dim]Interactive picker unavailable: not running in a TTY[/dim]")
                    except Exception:
                        pass
                    # Fallback to simple numeric prompt
                    options = [mode_label(m) for m in valid_modes]
                    console.print("Select mode:\n" + "\n".join(f"[{i+1}] {opt}{'  (current)' if valid_modes[i]==mode else ''}" for i,opt in enumerate(options)))
                    try:
                        choice = input("Mode > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[dim]Cancelled[/dim]")
                        continue
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(valid_modes):
                            mode = valid_modes[idx]
                            console.print(f"Mode set to: {mode_label(mode)}")
                            show_status()
                        else:
                            console.print("Invalid selection.")
                    else:
                        nm = choice.lower()
                        if nm in valid_modes:
                            mode = nm
                            console.print(f"Mode set to: {mode_label(mode)}")
                            show_status()
                        else:
                            console.print("Invalid mode name.")
                    continue

                # Otherwise parse sub-commands
                sub = parts[1].lower()
                if sub == "help":
                    console.print(
                        """
/mode                 Show current mode
/mode help            Show this help
/mode status          Show current mode and hint
/mode <name>          Set mode (natural, topic, verses, concordance, keyword)
/mode default [name]  Save default mode for future sessions
                        """.strip()
                    )
                    continue
                if sub == "status":
                    console.print(f"Current mode: [bold]{mode_label(mode)}[/bold]")
                    if mode == "natural":
                        console.print("Type questions normally (e.g., Why is Sabbath important?).")
                    elif mode == "topic":
                        console.print("Topical search across sources. Type keywords or short phrases.")
                    elif mode == "verses":
                        console.print("Verse lookup (e.g., John 3:16 or Gen 1:1-3).")
                    elif mode == "concordance":
                        console.print("Concordance mode. Type a word to see occurrences and contexts.")
                    elif mode == "keyword":
                        console.print("Keyword mode. Full-text lexical search across translations.")
                    continue
                if sub == "default":
                    new_mode = parts[2].lower() if len(parts) > 2 else mode
                    if new_mode not in valid_modes:
                        console.print("Invalid mode. Use one of: natural, topic, verses, concordance, keyword")
                        continue
                    settings["default_mode"] = new_mode
                    save_settings(settings)
                    console.print(f"Saved default mode: {mode_label(new_mode)}")
                    continue
                # Interactive picker if no name supplied
                if len(parts) == 1:
                    # Try curses-based interactive picker first
                    picked = interactive_mode_picker(valid_modes, current=mode)
                    if picked:
                        mode = picked
                        console.print(f"Mode set to: {mode_label(mode)}")
                        show_status()
                        continue
                    # Explain why picker didn't appear
                    try:
                        import sys as _sys
                        if curses is None:
                            console.print("[dim]Interactive picker unavailable: curses not available[/dim]")
                        elif not (_sys.stdin.isatty() and _sys.stdout.isatty()):
                            console.print("[dim]Interactive picker unavailable: not running in a TTY[/dim]")
                    except Exception:
                        pass
                    # Fallback to simple numeric prompt
                    options = [mode_label(m) for m in valid_modes]
                    console.print("Select mode:\n" + "\n".join(f"[{i+1}] {opt}{'  (current)' if valid_modes[i]==mode else ''}" for i,opt in enumerate(options)))
                    try:
                        choice = input("Mode > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[dim]Cancelled[/dim]")
                        continue
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(valid_modes):
                            mode = valid_modes[idx]
                            console.print(f"Mode set to: {mode_label(mode)}")
                            show_status()
                        else:
                            console.print("Invalid selection.")
                    else:
                        nm = choice.lower()
                        if nm in valid_modes:
                            mode = nm
                            console.print(f"Mode set to: {mode_label(mode)}")
                            show_status()
                        else:
                            console.print("Invalid mode name.")
                    continue
                # Direct set
                name = parts[1].lower()
                if name not in valid_modes:
                    console.print("Invalid mode. Use: natural, topic, verses, concordance, keyword")
                    continue
                mode = name
                console.print(f"Mode set to: {mode_label(mode)}")
                show_status()
                continue
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
                    show_status()
                    continue
                if action == "on":
                    ai_enabled = True
                    history.update_session_ai_enabled(session_id, True)
                    show_status()
                    continue
                if action == "off":
                    ai_enabled = False
                    history.update_session_ai_enabled(session_id, False)
                    show_status()
                    continue
                if action == "status":
                    show_status()
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
                    show_status()
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
                    show_status()
                    continue
                console.print("Unknown /ai subcommand. Try /ai status")
                continue
            if cmd == "gpu":
                info = db.device_info()
                console.print("GPU / Embedding Status:")
                console.print(json.dumps(info, indent=2))
                # Ollama hints
                opts = {}
                num_gpu = os.environ.get("TINYOWL_OLLAMA_NUM_GPU") or os.environ.get("OLLAMA_NUM_GPU")
                if num_gpu:
                    opts["num_gpu"] = num_gpu
                raw = os.environ.get("TINYOWL_OLLAMA_OPTIONS")
                if raw:
                    opts["options_env"] = raw
                if opts:
                    console.print("Ollama options (env):")
                    console.print(json.dumps(opts, indent=2))
                else:
                    console.print("[dim]No Ollama GPU options set (optional)[/dim]")
                continue
            if cmd.startswith("root"):
                parts = cmd.split()
                cur = settings.get("root_display", "auto")
                if len(parts) == 1 or parts[1] in ("help","status"):
                    console.print(f"[dim]Root panel: {cur} (options: auto, always, off)[/dim]")
                    continue
                choice = parts[1].lower()
                if choice not in ("auto","always","off"):
                    print_error("Invalid root setting. Use: /root auto|always|off")
                    continue
                settings["root_display"] = choice
                save_settings(settings)
                console.print(f"[dim]Root panel saved: {choice}[/dim]")
                continue
            if cmd == "history":
                start = time.perf_counter()
                with console.status("Loading history…", spinner="dots"):
                    sessions = history.recent_sessions(limit=10)
                for sid, created, ai in sessions:
                    console.print(f"Session {sid} — {created} — AI={'ON' if ai else 'OFF'}")
                console.print(f"[dim]Loaded in {(time.perf_counter()-start)*1000:.0f} ms[/dim]")
                continue
            if cmd.startswith("export"):
                from .config import EXPORTS_DIR
                EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
                with console.status("Exporting…", spinner="dots"):
                    msgs = history.get_session_messages(session_id)
                out = []
                for role, content, ts in msgs:
                    out.append({"role": role, "content": content, "time": ts})
                path = EXPORTS_DIR / f"session_{session_id}.json"
                start = time.perf_counter()
                path.write_text(json.dumps(out, indent=2))
                console.print(f"Exported to {path} [dim]{(time.perf_counter()-start)*1000:.0f} ms[/dim]")
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
                    with console.status("Loading more matches…", spinner="dots"):
                        pass
                    print_concordance_results(last_results_cache.get("word", ""), items, show=show_next)
                    last_results_cache["shown"] = show_next
                    continue
                if last_results_cache.get("kind") == "lexical":
                    items = last_results_cache.get("items", [])
                    shown = last_results_cache.get("shown", 0)
                    show_next = min(shown + 10, len(items))
                    with console.status("Loading more results…", spinner="dots"):
                        pass
                    print_keyword_results(last_results_cache.get("term", ""), items, show=show_next)
                    last_results_cache["shown"] = show_next
                    continue
            q = parsed.value
            # Mode-driven dispatch
            if mode == "concordance":
                word = q
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
            if mode == "keyword":
                term = q
                with console.status("Keyword search…", spinner="dots"):
                    items = db.lexical_search(term)
                print_keyword_results(term, items, show=10)
                last_results_cache = {"kind": "lexical", "term": term, "items": items, "shown": 10}
                history.add_message(session_id, "user", f"!{term}")
                continue
            if mode == "verses":
                ref = q
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
            # In natural/topic, try to surface Strong's root for a primary keyword first
            def _extract_primary_keyword(text: str) -> str:
                stop = {"what","is","the","and","or","of","to","in","a","an","on","for","with","does","do","bible","about","according","who","why","how"}
                toks = [t.strip(".,!?;:\"'()[]{}").lower() for t in text.split()]
                cand = [t for t in toks if t.isalpha() and len(t) >= 3 and t not in stop]
                # Prefer the first candidate
                return cand[0] if cand else ""

            if should_show_root_panel(q):
                primary = _extract_primary_keyword(q)
                if primary:
                    nums = db.get_strongs_for_keyword(primary)
                    if nums:
                        entries = db.get_strongs_entries(nums)
                        if entries:
                            print_strongs_root(primary.upper(), entries)
            # natural/topic path (both use routed_search with AI enhancement)
            with console.status("Searching across sources…", spinner="dots"):
                results = db.routed_search(q)
            print_router_results(q, results, show=5)
            history.add_message(session_id, "user", q if mode == "natural" else f"#{q}")
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
