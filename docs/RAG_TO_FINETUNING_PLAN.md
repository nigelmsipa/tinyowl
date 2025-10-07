# RAG → Fine‑Tuning Plan (Hybrid Strategy)

This plan outlines how TinyOwl evolves from a pure RAG system to a hybrid approach with a fine‑tuned model while keeping retrieval as a first‑class safety net.

## Objectives
- Preserve RAG strengths (freshness, provenance, long‑context grounding).
- Add a fine‑tuned model for better style, cohesion, and low‑context answers.
- Keep citations and source fidelity (Bible ≥ SOP ≥ commentary).

## Scope (Initial Theology Set)
- Bible: KJV, WEB
- SOP: Conflict of the Ages + Steps to Christ (complete)
- Ministries: Secrets Unsealed, Amazing Facts, 3ABN (complete)
- Series: Total Onslaught (lectures complete; paragraphs embedding in progress)

## Data Pipeline (Training Data)
1. Source curation
   - Filter out front matter, dupes, and very short fragments (< 120 chars for paras).
   - Keep paragraph/lecture level units as atomic examples.
2. Instruction templates (JSONL)
   - QA (short answer): question, context (top‑k chunks), answer, citations.
   - Long‑form (explanation): prompt, context, outline, answer, citations.
   - Style: “EGW‑inspired tone” preset (never claim authorship; always cite).
3. Generation strategy
   - Seed curated questions (doctrinal, exegetical, historical, practical).
   - Use RAG to assemble top‑k contexts → draft answers → human filter pass.
   - Add contrastive negatives (near‑miss contexts) for robustness.
4. Quality gates
   - Deduplicate by semantic hash; drop contradictory or low‑confidence answers.
   - Enforce max lengths; ensure every answer includes citations.
5. Splits
   - Train/val/test by book/series to avoid leakage (e.g., hold‑out DA chapters).

## Model & Training
- Base: TinyLlama (1.1B/3B) or Qwen2.5‑3B (empirically strong on Bible text).
- Method: LoRA/QLoRA adapters; bf16 if GPU permits; otherwise 8‑bit.
- Hyperparams (starting point)
  - lr: 2e‑4 (linear), warmup 5%, weight decay 0.01
  - seq_len: 2k (expand after stability), batch: 64 eff (grad accumulate)
  - epochs: 2–3 (SFT), early stop on val loss/ROUGE BLEU plateau
- Hardware
  - ROCm/CUDA single‑GPU (24–32GB vRAM) or multi‑GPU if available.
- Checkpointing
  - Save every N steps; keep best by val composite (loss + citation ratio).

## Evaluation
- Automatic
  - Answer faithfulness (n‑gram overlap vs sources), citation presence/precision.
  - Style adherence classifier (EGW‑inspired; no false authorship claims).
  - RAG‑free accuracy on short questions; hybrid accuracy on long questions.
- Human review
  - Pastor/teacher checklist on tone, accuracy, balance (Bible ≥ SOP ≥ commentary).
  - “Red team” theology traps; verify model avoids speculation.

## Serving & Orchestration
- Default: Hybrid
  - Try RAG‑only → If context insufficient, fall back to fine‑tuned model with compact prompt.
  - Or use fine‑tuned model to draft, then constrain with RAG snippets (citation anchoring).
- Controls
  - /mode hybrid|rag|ft to pick behavior per session.
  - Always render citations with source and section.

## Safety & Policy
- Never present as Ellen G. White; “in the manner of,” with clear attribution.
- Do not fabricate references; prefer silence over speculation.
- Keep Bible primacy; SOP supportive; commentary clearly labeled.

## Milestones
- M0: Dataset spec + sampler (JSONL writers)
- M1: 50k SFT pairs (QA + long‑form) from Bible + SOP core
- M2: LoRA baseline (TinyLlama/Qwen 3B) with faithful citations
- M3: Hybrid router integration + A/B vs RAG‑only
- M4: Add ministries + Total Onslaught to training set
- M5: Release v1 Hybrid (CLI toggle + eval report)

## Work Items (Initial)
- [ ] scripts/dataset/build_sft_jsonl.py (from chunks + RAG retrieval)
- [ ] scripts/dataset/filters.py (dedupe, length, citation checks)
- [ ] scripts/train/finetune_lora.py (TinyLlama/Qwen PEFT harness)
- [ ] chat_app: /mode ft|hybrid|rag + style preset (/style egw)
- [ ] eval: automatic + small human rubric in docs/EVAL.md

## Appendix
- See docs/PIPELINE.md for end‑to‑end pipeline.
- See README.md for roadmap and project vision.

