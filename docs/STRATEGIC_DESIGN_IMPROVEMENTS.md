# TinyOwl — Strategic Design Improvements

Last updated: ${DATE:-2025-09-24}

## Executive Summary

TinyOwl has strong building blocks for a focused theological RAG assistant with both AI and concordance-only modes. The biggest wins now are to: (1) solidify boundaries between ingestion, retrieval, and chat layers; (2) make data/config/state deterministic and reproducible; (3) tighten UX and observability for reliability; and (4) reduce operational toil with automation and CI.

## Guiding Principles

- Single source of truth for configuration and paths.
- Deterministic, reproducible pipelines and indexes.
- Clear module boundaries with typed interfaces.
- Fast feedback: tests, profiling, and metrics by default.
- Offline-first capability with concordance fallback.

## High-Priority Improvements (0–30 days)

1) Architecture & Modularity
- Extract clear domains:
  - `ingestion/` (ETL, chunking, embeddings)
  - `retrieval/` (vector/hybrid search, rerank)
  - `chat/` (UI, prompts, sessions)
  - `core/` (config, logging, types, utils)
- Refactor `tinyowl/chat_app/main.py` (~500+ lines) into components:
  - Command parser, Session manager, Renderer, Router (AI vs concordance)
- Introduce typed boundaries (PEP 561, `mypy`) and `dataclasses`/`pydantic` models for internal data (chunks, hits, citations).

2) Configuration & Environments
- Promote `tinyowl/chat_app/config.py` into `core/config.py` using `pydantic-settings` (`BaseSettings`) with env var overrides.
- Standardize env keys: `TINYOWL_*` only; deprecate duplicates. Document all in README.
- Provide `configs/` per-domain YAML(s) (e.g., `domains/theology/config.yml`) driving chunking, embed model, metadata schema, stopwords.

3) Data & Ingestion Pipeline
- Make ingestion idempotent and declarative:
  - One config file defines sources, normalization, tokenization, chunking tiers, embeddings.
  - Content hashing + versioned outputs (`vectordb/<domain>/<version>/...`).
- Persist provenance and lineage (source path, checksums, transform versions) on every chunk.
- Add validators: file-type, canonicalization, chapter/verse integrity, reference resolver.
- Add `make ingest` targets and smoke tests for each domain.

4) Retrieval Quality & Speed
- Hybrid retrieval (BM25 + vector) with tunable weights; cache top-k doc ids.
- Rerank step (e.g., `bge-reranker` via local Ollama or on-CPU tiny model) behind a feature flag.
- Deterministic query pre-processing (strip refs, normalize Greek/Hebrew variants where applicable).
- Enforce metadata schema (book, chapter, verse/pericope, source, edition) for filterable queries.

5) Chat UX (CLI)
- Unify command syntax and help:
  - `/help`, `/model`, `/topk`, `/mode [ai|concordance]`, `/save`, `/load`, `/clear`
- Inline examples and discoverability; contextual tips after errors.
- Session transcript management with `~/.local/state/tinyowl/` files already configured — add import/export.
- Concordance-only mode explicit toggle and clear indicator in the prompt.

## Medium-Priority Improvements (30–60 days)

6) Observability & Reliability
- Structured logging (`structlog` or JSON) with correlation ids per query.
- Minimal metrics: latency, hit counts, token counts, cache hit rate.
- Trace retrieval pipeline stages (ingest→retrieve→rerank→compose) with timing breakdowns.

7) Performance & Resource Use
- GPU detection and graceful fallback in `launch_*` scripts; print active device and memory.
- Embedding/ingest batching; async I/O for file reads and network calls.
- Vector DB lifecycle: periodic compaction, vacuum, and backup rotation for `vectordb/`.
- Cache prompt templates and pre-tokenize scripture references.

8) Testing Strategy
- Unit tests for chunking and reference parsing.
- Golden tests for retrieval (stable inputs/outputs pinned).
- CLI smoke tests for chat startup and command parsing.
- Property tests for verse/reference normalization (e.g., `&john3:16`, `#prophecy`).

## Longer-Term (60–90 days)

9) Prompting & Answer Composition
- Domain-specific prompt library with versioned templates; cite verses explicitly.
- Structured citations object in final answer; render cleanly in CLI.

10) Packaging & Distribution
- Convert to installable package: `pip install -e .` with console scripts (`tinyowl`, `tinyowl-chat`).
- Optional extras: `[gpu]`, `[dev]`, `[docs]`.

11) CI/CD & Dev Experience
- `pre-commit` with `ruff`, `black`, `isort`, `mypy`.
- GitHub Actions: lint + tests + (optional) build artifacts.
- `Makefile` for common tasks (`setup`, `ingest`, `chat`, `test`).
- Devcontainer for consistent local setup.

## Concrete, File-Scoped Suggestions

- `tinyowl/chat_app/main.py`
  - Split into modules: `commands.py`, `session.py`, `renderer.py`, `router.py`.
  - Add `/mode` switch and per-session settings (model, top_k, domain).
  - Stream tokens with clear status lines and elapsed time.

- `tinyowl/chat_app/config.py`
  - Replace ad-hoc env reads with `BaseSettings`; document `TINYOWL_...` keys.
  - Support `XDG_*` paths consistently; keep history/state under `chat-app/` as designed.

- `tinyowl/scripts/tinyowl_query.py`
  - Extract a reusable `RetrievalRouter` class; share with chat app to avoid duplication.
  - Normalize query parsing and verse-reference resolution into `core/refs.py`.

- `tinyowl/configs/` (exists)
  - Add per-domain YAMLs driving ingestion and retrieval defaults; commit one for `theology`.

- `tinyowl/vectordb/`
  - Introduce domain/version subfolders; add `MANIFEST.json` with schema + checksum + timestamp.
  - Add cleanup/backup scripts and a README for operational tasks.

- `tinyowl/requirements.txt`
  - Pin versions and add a `requirements-dev.txt` for tooling.
  - Consider a `constraints.txt` to stabilize transitive deps.

- Tests (`tinyowl/tests/`)
  - Add golden retrieval tests and CLI smoke tests.
  - Add ingestion validators to catch malformed verse ranges or mis-ordered chapters.

## 30-60-90 Roadmap

- 0–30 days (Quick Wins)
  - Standardize config with `BaseSettings` and env docs.
  - Split chat app by concern; add `/help` and `/mode` commands.
  - Add ingestion idempotency with hashing and manifests.
  - Introduce structured logging and basic metrics.

- 30–60 days
  - Hybrid search + optional rerank; schema filters.
  - Golden tests for retrieval; CLI smoke tests in CI.
  - GPU detection and graceful fallback; resource usage logs.

- 60–90 days
  - Package CLI entry points; devcontainer.
  - Comprehensive docs with architecture diagrams and runbooks.
  - Performance profiling and index compaction job.

## Quick-Start Checklist

- [ ] Create `core/` with `config.py`, `logging.py`, `types.py`.
- [ ] Refactor `chat_app/main.py` into smaller modules; add `/mode`, `/help`.
- [ ] Add `domains/theology/config.yml` and wire ingestion to use it.
- [ ] Write chunk/ingest validators and provenance recording.
- [ ] Implement hybrid retrieval (BM25 + vector) behind a flag.
- [ ] Add structured JSON logs and minimal metrics.
- [ ] Introduce `pre-commit` with `ruff`/`black`/`mypy`.
- [ ] Write golden retrieval tests and CLI smoke tests.

---

Questions or preferences on priorities? See `tinyowl/CLAUDE.md` and `RAG_TEST_RESULTS.md` for current context; this plan complements those with concrete engineering steps and sequencing.

