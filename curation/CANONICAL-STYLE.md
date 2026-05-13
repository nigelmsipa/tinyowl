# Canonical Answer Style Guide

This file governs how all `canonical-NNN.md` files are written and reviewed. Read it before generating or editing any canonical entry.

---

## Purpose of the corpus

This is a multi-layered theological Q&A resource drawn from real questions asked of SDA speakers (I'd Like to Know, 3ABN, Amazing Facts, Randy Skeete, C.D. Brooks, etc.) and from written sources (Ron Rhodes, *Big Book of Bible Answers*). Each answer is not a transcript summary — it is a fully argued, scripture-grounded response that happens to be traceable to a source.

The corpus serves as:
- A **catechetical drill** — listen to questions, recall the argument
- A **teaching tool** — see how biblical arguments are constructed from first principles
- A **pastoral reference** — when the question comes up in real life, here is a trustworthy answer
- A **searchable app** — filterable by layer, theme, scripture, speaker

---

## File structure

```
# canonical-NNN

[header metadata]

## Entry `canonical-NNNa`

[entry metadata]

### Answer

[the answer — 4 layers]

## Entry `canonical-NNNb`   ← only if the episode had a second distinct question

[entry metadata]

### Answer

[the answer — 4 layers]

## Fidelity notes

[sourcing transparency — one paragraph per entry]
```

---

## Header metadata fields

| Field | What it is |
|---|---|
| `source_id` | Source series slug (e.g. `id-like-to-know`) |
| `canonical_sequence` | Zero-padded episode number (`001`, `002`, …) |
| `title` | Episode title as published |
| `speaker` | Speakers in episode |
| `video_id` | YouTube video ID |
| `transcript_source` | Relative path to the `.en-orig.vtt` file |
| `derived_entries` | How many entry blocks this file contains |

---

## Entry metadata fields

| Field | What it is |
|---|---|
| `question` | The exact question answered — stated cleanly, not quoted from the questioner's rambling |
| `scripture_basis` | Semicolon-separated list of the key passages the answer actually rests on |
| `source_scripture_usage` | **Critical** — records exactly how each scripture was used in the source (read directly, paraphrased, referenced without reading, or cited by topic only). This is the traceability record. Never conflate "mentioned" with "read directly." |
| `secondary_support` | Named non-scripture sources (EGW works with volume/page, named scholars, named books) |
| `tags` | Comma-separated lowercase slugs |

---

## The four answer layers

Every answer has four labeled sections in this order. Do not reorder them. Do not merge them.

### `**Scripture**`

The biblical argument. Work from the actual text — show the reasoning, not just the conclusion. If the identification of a prophecy requires steps (e.g. beast = papacy), show the steps concisely. A reader without background should be able to follow the logic. If the full argument is too long to develop inline, give the compressed version and point to the resource (e.g. "*(For the full argument see The Great Controversy, chapter X.)*").

If no scripture governs the question (rare — e.g. a question about church practice with no direct biblical text), write: "No scripture governs this question directly" and explain what principle does govern it. Do not paste in thematic verses that were never part of the argument.

### `**Spirit of Prophecy**`

Ellen White's relevant contribution. Cite the specific work and location when known. If the source transcript read a passage directly on air, quote or closely paraphrase it here. If the SOP layer is curator-supplied (not from the source transcript), note it in the fidelity notes — do not pretend it came from the speakers.

### `**Historical / Scholarly**`

Historical context, scholarly background, or extra-biblical documentation that grounds the argument. This is where you place: patristic sources, archaeological or historical evidence, documented scholarly positions, named theologians. If the source transcript named a scholar or book, include it here. If it is curator-supplied, note it in fidelity notes.

### `**Pastoral**`

The human application. What does this mean for the person asking? What is the practical, lived implication? This layer often draws directly from what the speakers said — their illustrations, anecdotes, and direct counsel. Keep it grounded. Avoid moralizing in the abstract.

---

## Voice and style

**Active, declarative, direct.** The answer states truth — it does not report on what speakers thought about truth.

❌ Wrong:
> "Bohr argues that the first beast represents the papacy."
> "The speakers make the point that haste creates shared guilt."
> "According to the transcript, this verse is about ordination."

✅ Right:
> "The first beast represents the papacy."
> "Haste creates shared guilt."
> "This verse is about ordination."

The speakers disappear into the background. Their arguments become the answer. Their sourcing lives in `source_scripture_usage` and fidelity notes.

**Logic must be tight.** Every claimed identification or doctrinal conclusion must be earned in the text. If you assert "the first beast = papal Rome," show why — even if briefly. Leaps will confuse a reader with no background. The standard is: a motivated newcomer should be able to follow every step.

**No filler layers.** If the SOP layer has nothing genuine to contribute for a particular question, say so briefly and keep it short. Do not invent EGW content. Do not fabricate citations. If you are unsure of a specific page or chapter, say "from [work], approximately [chapter]" or omit the citation and note the uncertainty in fidelity notes.

**Narration ≠ endorsement.** When Scripture describes something (Gibeonites deceiving Israel, the prophet's disguise in 1 Kings 20), that description is not a prescription. Make the distinction explicit when the question requires it.

---

## Fidelity notes

One paragraph per entry, at the end of the file. Its purpose is sourcing transparency — it records:
- What was read directly on air vs. paraphrased vs. referenced without reading
- What was added by the curator (not in the source transcript) and why
- Any interpretive choices made in the answer (what was included, what was left out, why)
- Anything the speakers said that the answer chose not to follow

Fidelity notes are not a summary of the answer. They are a sourcing audit.

---

## Common mistakes to avoid

1. **Speaker attribution in the answer body** — "Bohr says," "the speakers note," "according to Murray." Never. Attribution lives in fidelity notes only.
2. **Fabricated citations** — do not invent EGW page numbers, scholar names, or book titles you are not confident about. Mark uncertainty explicitly.
3. **Unsupported leaps** — asserting prophetic identifications or doctrinal conclusions without showing the reasoning steps.
4. **Filling empty layers** — a question about church practice does not have a scripture layer. Say so. Do not pad.
5. **Turning the pastoral layer into abstraction** — the pastoral layer should be concrete, immediate, and applied. It should feel like counsel, not a homily.
6. **Conflating description and prescription in Scripture** — always distinguish what the text reports from what it commands.

---

## Source material

| Layer | Where it comes from |
|---|---|
| Scripture | The transcript (what was actually read/cited) + curator's biblical argument |
| Spirit of Prophecy | The transcript (if EGW was quoted) + NotebookLM SOP pass output |
| Historical / Scholarly | The deep research pass output + what the speakers named |
| Pastoral | Primarily the source transcript — what the speakers actually said |

The pastoral layer is the one layer most grounded in the source transcript. If the transcript did not address pastoral application, keep it short rather than inventing application.

---

## On deduplication

Many questions recur across sources (ILK, 3ABN, AF, Randy Skeete, etc.). Deduplication will happen after all source research passes are complete. Until then, each source gets its own canonical treatment so that the pastoral layer preserves the voice and argument of that specific speaker. The same question answered by Stephen Bohr and by Randy Skeete will produce different pastoral layers — both are valuable.
