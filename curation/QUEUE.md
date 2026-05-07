# Tiny Owl Curation Queue

## Now

- Current priority is Q&A-first corpus work.
- The older 3ABN SRT batch has been retired from the active queue and will be replaced by a NotebookLM export.

- **I'd Like to Know**
  - `id`: `id-like-to-know`
  - `status`: `in_progress`
  - `raw`: `/home/nigel/NotebookLM_Extract/Takeout/NotebookLM/I_d Like to Know _ Q&A/Sources`
  - `output`: `curation/curated/id-like-to-know`
  - `scope`: `230` source files
  - `index`: `curation/curated/id-like-to-know/INDEX.md`

- **C.D. Brooks - Questions & Answers**
  - `id`: `cd-brooks-qa`
  - `status`: `queued`
  - `raw`: `/home/nigel/NotebookLM_Extract/Takeout/NotebookLM/_          C.D. Brooks - Questions & Answers,  Pt./Sources`
  - `output`: `curation/curated/cd-brooks-qa`

- **Bible Answers Live / Amazing Facts Q&A**
  - `id`: `amazing-facts-qa`
  - `status`: `queued`
  - `raw`: `/home/nigel/NotebookLM_Extract/Takeout/NotebookLM/Bible Answers Live_ Essential Theological Question/Sources`
  - `output`: `curation/curated/amazing-facts-qa`

- **Ellen White writings collection**
  - `id`: `ellen-white-writings`
  - `status`: `queued`
  - `raw`: `/home/nigel/NotebookLM_Extract/Takeout/NotebookLM/Spirit of prophecy/Sources`
  - `output`: `curation/curated/ellen-white-writings`
  - `scope`: `124` source pairs of Ellen White books from the White Estate corpus

- **Defense of the Prophet lecture series**
  - `id`: `defense-of-the-prophet`
  - `status`: `queued`
  - `raw`: `/home/nigel/NotebookLM_Extract/Takeout/NotebookLM/Spirit of Prophecy /Sources`
  - `output`: `curation/curated/defense-of-the-prophet`
  - `scope`: `17` lecture/transcript source pairs defending Ellen White

## Workflow states

- **queued** — source identified but untouched
- **in_progress** — currently being curated
- **curated** — entries extracted and cleaned
- **reviewed** — checked for fidelity and attribution
- **loaded** — imported into the app database
- **blocked** — waiting on a file, clarification, or cleanup issue

## Curation rule

We are allowed to clean spoken material for readability.
We are not allowed to rewrite the theology.

That means:

- remove filler words
- remove repeated spoken clutter
- fix obvious spoken-to-written awkwardness
- keep the actual claim intact
- keep attribution intact
- keep the source trail intact

Operational clarifications from live curation:
- numbering tracks the source file being worked, not the count of final derived entries
- one source file may produce multiple Q&A entries if the raw episode contains multiple real questions
- default answer voice is direct and non-meta, not `the panel says` or `the answer is`
- preserve Scripture as the primary reasoning layer
- mark Ellen White or similar material as secondary support when the source uses it that way
- make the reasoning path visible enough that the reader can see how the answer is formed
- compress strongly for clarity and force, but do not invent anything the source did not actually argue

## Answer prose standard

The answer is not a theological summary. It is a scripture-driven argument.

Every cited scripture must appear explicitly in the prose — named by reference and engaged
with directly. The scripture is not decoration. It is the spine of the logic. The reader
must be able to see: here is the text, here is what it says, here is what that means, here
is where the argument goes next.

Wrong:
> Perfection does not mean maintenance-free. God gave Adam purposeful labor as a gift.

Right:
> Genesis 2:15 places Adam in the garden "to tend and keep it." The word keep implies
> ongoing maintenance, not a one-time act. After the Fall, Genesis 3:19 reframes the same
> labor — "in the sweat of your face you shall eat bread" — which only makes sense as a
> contrast if pre-Fall work was already real, just without the curse.

Rules:
- name the scripture reference before or as you use it
- quote or paraphrase the actual text, don't just assert what it means
- let the argument move forward from the text, not around it
- if the source builds from multiple texts, show the chain
- Ellen White and secondary sources follow scripture, they do not lead it
- under 200 words per answer; force makes it shorter, not longer
