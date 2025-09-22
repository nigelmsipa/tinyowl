# TinyOwl Chat — Ollama Integration Plan

## Current State
- Basic non‑streaming enhancement via `enhance_with_ai()` calling Ollama `/api/generate` with `stream=false`.
- Health check via `/api/tags` to toggle AI availability.
- Default model defined in `chat_app/config.py` (`DEFAULT_AI_MODEL = "mistral:latest"`).
- CLI supports `/ai toggle`; integrates AI summaries for `#topic` and free‑text queries.

## Goals
- Robust, configurable, and user‑controllable Ollama integration that degrades gracefully when Ollama is unavailable.

## Planned Features
- Model management
  - List installed models from `/api/tags`.
  - Switch model at runtime: `/ai model <name>` with validation.
  - Config overrides: env `TINYOWL_OLLAMA_MODEL` and persisted session default.
- Streaming responses
  - Add streaming generator using `/api/generate` with `stream=true`.
  - Progressive display in CLI with clean rendering and cancel (Ctrl+C) support.
- Commands and status
  - `/ai on`, `/ai off`, `/ai toggle`, `/ai status`, `/ai model <name>`, `/ai models`.
- Error handling and resilience
  - Timeouts, retries (short backoff), and clear user messages.
  - Graceful fallback to non‑AI output when errors occur.
- Prompting and citations
  - Keep strict grounding to retrieved context; preserve [index] citations.
  - Cap token/ctx by truncating context as needed.
- Persistence
  - Persist AI enabled flag and selected model per session in `ChatHistory`.

## Implementation Steps
1. Config
   - Add env overrides: `TINYOWL_OLLAMA_MODEL`, `TINYOWL_OLLAMA_HOST` to `chat_app/config.py`.
   - Expose `OLLAMA_HOST` (default `http://localhost:11434`) and `DEFAULT_AI_MODEL` deriving from env.
2. Integration helpers (`chat_app/ollama_integration.py`)
   - Add `list_models(host) -> list[str]` using `/api/tags`.
   - Add `generate_stream(prompt, model, host, timeout)` yielding text chunks; fallback to non‑streaming.
   - Centralize error handling + timeouts.
3. Commands (`chat_app/command_parser.py`)
   - Extend to parse: `ai on|off|toggle|status`, `ai model <name>`, `ai models`.
4. Main loop (`chat_app/main.py`)
   - Wire new commands; display status and current model.
   - Use streaming path for AI summaries with interrupt handling; fallback to non‑streaming if needed.
   - Persist `ai_enabled` and `ai_model` to session via `ChatHistory`.
5. Tests (lightweight)
   - Parser unit tests for `/ai` subcommands.
   - Integration tests with mocked HTTP for `list_models` and streaming generator.
6. Docs
   - Update `README.md` (Chat usage) with `/ai` commands, env vars, and examples.
   - Update `launch_tinyowl_chat.sh` banner to mention `/ai` commands.

## Acceptance Criteria
- `/ai status` reports availability and current model.
- `/ai models` lists models; `/ai model <name>` validates and switches model.
- When streaming is enabled, responses display progressively and can be interrupted without crashing.
- Errors (connection refused, timeout) surface as concise messages and do not break core search features.
- Env var `TINYOWL_OLLAMA_MODEL` overrides default; absence reverts to config default.

## Rollback Plan
- Feature‑flag via the existing `ai_enabled` toggle; if issues arise, instruct users to `/ai off`.
- Code changes isolated to `chat_app/` with no DB migrations.

## Notes
- Keep prompts concise and strictly grounded in retrieved context to avoid hallucinations.
- Do not block core concordance/verse features on Ollama availability.
