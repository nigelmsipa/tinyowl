# Tiny Owl

Tiny Owl is a local-first theological Q&A database.

It is not a chatbot.
It is not a cloud product.
It is not a local-LLM playground.

The job is simple:

- curate raw theological material into clean Q&A entries
- store them in a deterministic local database
- retrieve them instantly with grounded search
- keep source attribution intact

## Direction

Tiny Owl is being rebuilt around a straightforward product thesis:

- local utility over hype
- deterministic retrieval over probabilistic chat
- grounded source material over synthetic theology
- elegant reading and search over backend complexity

The long-term application shape is a local desktop app backed by SQLite FTS.
But the immediate work is corpus work.

## What we are building first

The first real asset is not the UI.
It is the corpus.

We are taking raw source material such as:

- video transcripts
- sermon transcripts
- Q&A recordings
- live call-in programs
- manually gathered notes and extracts

And turning them into structured entries with:

- `question`
- `answer`
- `tags`
- `speaker`
- `source`
- `series`
- `timestamp` or other citation anchor when available

## Curation standard

This project requires editorial cleanup, but not theological rewriting.

That means:

- remove filler words
- remove repeated verbal clutter
- tighten phrasing for readability
- preserve the speaker's actual argument
- preserve doctrinal meaning
- preserve attribution
- preserve traceability back to the source

In live curation work, this now means the following more specific rules:

- number source files for workflow, but do not assume one source file equals one final Q&A entry
- allow one source file to yield multiple entries when the episode contains multiple real questions
- write answers in direct, non-meta voice rather than curator-summary voice
- keep Scripture as the center of gravity in the answer
- show the reasoning spine clearly enough that the reader can see how the answer is built
- treat Ellen White or similar material as secondary support when the source itself uses it that way
- refactor strongly for clarity, force, and flow, but do not invent claims, premises, or conclusions
- preserve not only what answer was given, but how a strong answer is formed

The goal is not to invent a better answer.
The goal is to convert spoken material into clean, searchable, citation-ready Q&A.

## Product principles

- local-first
- offline-capable
- source-grounded
- keyboard-fast
- small and durable
- no cloud dependency for core retrieval
- no fake AI shell around a weak corpus

## Likely stack

For the app layer:

- Tauri
- Rust backend
- SQLite with FTS5

For the data layer:

- normalized entry metadata
- denormalized FTS search table
- deterministic scripture and source references

## Curation system

The repository now tracks corpus work explicitly.

- `curation/sources.json` — machine-readable source catalog
- `curation/QUEUE.md` — human-readable work queue
- `curation/curated/id-like-to-know/` — curated output for Stephen Bohr's "I'd Like to Know"
- `curation/curated/cd-brooks-qa/` — curated output for C.D. Brooks Q&A
- `curation/curated/amazing-facts-qa/` — curated output for Bible Answers Live / Amazing Facts Q&A

Each source moves through these states:

- `queued`
- `in_progress`
- `curated`
- `reviewed`
- `loaded`
- `blocked`

## Initial source queue

- `id-like-to-know` — Stephen Bohr / NotebookLM extraction
- `cd-brooks-qa` — C.D. Brooks / NotebookLM extraction
- `amazing-facts-qa` — Doug Batchelor / Bible Answers Live / NotebookLM extraction

## Immediate next steps

- ingest raw files
- curate them into clean Q&A records
- define the minimal canonical schema
- compile the first local database
- build the smallest useful search interface

## Non-goals for now

- chatbot UX
- cloud APIs
- vector search as the core retrieval layer
- training local models as the primary product
- overbuilt backend services

## Repository status

This repository was intentionally cleared to remove the previous local-LLM and RAG baggage.

We are rebuilding Tiny Owl from a clean slate around a deterministic theological database and a serious curation workflow.
