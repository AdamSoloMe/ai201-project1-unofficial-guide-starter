# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

CUNY Queens College Computer Science professor reviews sourced from Rate My Professors. This knowledge is valuable because official Queens College course catalogs describe what a course covers, not what it is actually like to sit through — they say nothing about exam difficulty, grading fairness, office hour availability, or teaching clarity. A student registering for CS212 or CS320 has no official way to learn whether the professor grades on a curve, whether lectures are useful, or how the workload compares to other sections. Rate My Professors aggregates exactly this kind of peer knowledge, but it requires visiting individual professor pages and reading through dozens of reviews manually. A RAG system makes it searchable: a student can ask "Is Alex Ryba a good professor?" and get a grounded answer drawn from real student reviews.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Alex_Ryba | 25 student reviews — CS212, CS313, CS320 (4.5/5.0, 150 ratings) | https://www.ratemyprofessors.com/professor/44623 |
| 2 | Jerry_Waxman | 25 student reviews — CS211, CS381 (3.4/5.0, 312 ratings) | https://www.ratemyprofessors.com/professor/287312 |
| 3 | Simina_Fluture | 25 student reviews — mixed CS courses (2.6/5.0, 276 ratings) | https://www.ratemyprofessors.com/professor/513427 |
| 4 | John_Svadlenka | 25 student reviews — CS211, CS340, CS370 (1.5/5.0, 164 ratings) | https://www.ratemyprofessors.com/professor/2485140 |
| 5 | Anne_SmithThompson | 25 student reviews — intro CS (2.9/5.0, 121 ratings) | https://www.ratemyprofessors.com/professor/352320 |
| 6 | Kent_Boklan | 25 student reviews — CS320 (2.5/5.0, 149 ratings) | https://www.ratemyprofessors.com/professor/629756 |
| 7 | Jackson_Yeh | 25 student reviews — CS240 (4.2/5.0, 76 ratings) | https://www.ratemyprofessors.com/professor/1082596 |
| 8 | Matthew_Fried | 25 student reviews — CS courses (4.0/5.0, 91 ratings) | https://www.ratemyprofessors.com/professor/1822595 |
| 9 | MdMahbubur_Rahman | 25 student reviews — CS courses (2.3/5.0, 87 ratings) | https://www.ratemyprofessors.com/professor/2649371 |
| 10 | Robert_Goldberg | 25 student reviews — CS courses (2.8/5.0, 86 ratings) | https://www.ratemyprofessors.com/professor/446485 |
| 11 | Paul_Cesaretti | 25 student reviews — CS courses (3.1/5.0, 59 ratings) | https://www.ratemyprofessors.com/professor/2354095 |
| 12 | Mayank_Goswami | 25 student reviews — CS courses (3.3/5.0, 44 ratings) | https://www.ratemyprofessors.com/professor/2195317 |
| 13 | Delaram_Kahrobaei | 23 student reviews — CS courses (3.9/5.0, 23 ratings) | https://www.ratemyprofessors.com/professor/2870283 |
| 14 | Russell_Gomes | 16 student reviews — CS courses (3.3/5.0, 16 ratings) | https://www.ratemyprofessors.com/professor/2913678 |
| 15 | Cuneyt_Akinlar | 25 student reviews — CSCI111, CSCI331, CSCI348 (4.9/5.0, 39 ratings) | https://www.ratemyprofessors.com/professor/2941773 |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Reasoning:**

Rate My Professors reviews are short — typically 50 to 250 characters each. A 600-character chunk (used for long-form documents like wiki articles) would merge 3–5 unrelated reviews from the same professor into a single embedding, diluting the semantic signal. The embedding would represent a blend of opinions rather than a specific viewpoint, making it harder to retrieve the right chunk for a targeted query like "what do students say about Ryba's grading?"

A 400-character chunk fits 1–3 reviews naturally. The chunker is paragraph-aware: it merges paragraphs until the 400-character limit is reached, then starts a new chunk with a 50-character tail of overlap. The 50-character overlap is small because individual reviews are self-contained — a review doesn't need context from the previous review to be understood. The overlap mainly guards against splitting a single long review mid-sentence.

Each document also opens with a professor metadata header (name, department, overall rating, difficulty, would-take-again percentage). This header is preserved in the first chunk of each document, so retrieval queries like "who is the highest-rated professor?" can match on the structured metadata.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 7

**Production tradeoff reflection:**

`all-MiniLM-L6-v2` was chosen because it runs locally — no API key, no rate limits, and fast enough for interactive use. For a production deployment serving students at scale, the main tradeoffs to consider:

- **Context length:** MiniLM is capped at 256 tokens. Short reviews fit comfortably within this limit, so truncation is rarely an issue for this specific corpus. For longer documents (syllabi, housing guides), a higher-limit model would matter more.
- **Domain specificity:** MiniLM is trained on general web text. Course codes like "CS31" or "CS111" are treated as character sequences rather than semantic identifiers. A model fine-tuned on educational or review-style text would produce better embeddings for course-specific queries.
- **Accuracy vs. cost:** OpenAI's `text-embedding-3-small` consistently outperforms MiniLM on retrieval benchmarks and would reduce the retrieval failures observed for vague queries (e.g., "which professor gives helpful feedback"), but it costs money per call.
- **Multilingual support:** Queens College has a significant international student population. A multilingual model would allow queries in Spanish, Chinese, or Korean to retrieve English-language reviews.

Top-k is set to 7. With 15 professors in the corpus, retrieving 7 chunks ensures a named professor's own reviews are surfaced even when another document mentions them in passing. 7 was chosen after observing that a query like "Is Waxman a good professor?" ranked Waxman's own chunks at position 6 due to a Russell Gomes review mentioning his name — top-5 would have missed him entirely.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which CS professor at Queens College is the most highly rated by students? | Cuneyt Akinlar (4.9/5.0, 39 ratings) or Alex Ryba (4.5/5.0, 150 ratings) — the system should name a specific professor with supporting rating data. |
| 2 | What do students say about Alex Ryba's teaching style and difficulty? | Reviews describe him as clear, organized, and engaging; uses real-world examples; records lectures; difficulty is manageable (2.5/5.0); 92% would take again. |
| 3 | Is Jerry Waxman a good professor for CS courses? | Mixed — some praise his lecturing, others find him hard to follow; overall rating 3.4/5.0 with 312 reviews; only 46% would take him again. |
| 4 | What do students complain about most in Queens College CS courses? | High difficulty with unfair grading (Boklan cited); disorganized lectures; heavy workloads — cited across Kent Boklan, John Svadlenka, and Simina Fluture reviews. |
| 5 | Which Queens College CS professor is easiest and which is hardest? | Easiest: Alex Ryba (2.5/5.0 difficulty) or Delaram Kahrobaei (2.5/5.0); Hardest: Kent Boklan (4.5/5.0) or John Svadlenka (4.3/5.0) — the system should cite difficulty ratings from the documents. |

---

## Anticipated Challenges

1. **Thin coverage for rarely-reviewed professors.** Several professors in the corpus have only a handful of reviews. A question specifically about Russell Gomes (16 ratings) or Delaram Kahrobaei (23 ratings) will retrieve minimal content — potentially just one chunk — which is not enough for the LLM to give a confident, detailed answer. The system will (correctly) say it doesn't have enough information, but this reveals a corpus coverage gap rather than a retrieval or generation failure.

2. **Comparative queries require cross-document reasoning.** Questions like "who is the easiest professor?" require the retrieval step to surface chunks from multiple professor documents, and the generation step to synthesize ratings across them. MiniLM embeddings don't inherently capture the comparative structure of the query — it retrieves chunks based on individual term similarity, not by understanding "compare professors." This means the retrieved chunks may not be the most relevant ones for answering the question as a whole.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OFFLINE PIPELINE                              │
│                                                                      │
│  ingest.py                       embed.py                            │
│  ┌──────────────────────┐        ┌──────────────────────────────┐   │
│  │  RMP GraphQL API     │ .txt   │ chunk_text()  SentenceTransf.│   │
│  │  (bGVzdDp0ZXN0 auth) │ ─────► │ 400 char /   all-MiniLM-L6  │   │
│  │                      │ files  │ 50 overlap   ─────────────►  │   │
│  │  15 Queens College CS          │        │              ChromaDB        │   │
│  │  professor pages     │        │              (persistent)    │   │
│  └──────────────────────┘        └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        QUERY PIPELINE                                │
│                                                                      │
│  app.py (Gradio)                                                     │
│  ┌──────────┐    query.py                                           │
│  │  User    │    ┌─────────────────────────────────────────────┐   │
│  │  Question│──► │ embed query → ChromaDB top-7 → build prompt │   │
│  │          │    │ (MiniLM)      semantic search   w/ context  │   │
│  │  Answer  │◄── │                                             │   │
│  │  Sources │    │ Groq API (llama-3.3-70b-versatile)         │   │
│  └──────────┘    │ grounded generation + source citation       │   │
│                   └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
Used Claude with the Documents table and Chunking Strategy section as input. Asked it to implement `ingest.py` using the RMP GraphQL API, with the correct `SchoolSearchQuery` object structure and base64-encoded `departmentID`. Also asked it to implement `chunk_text()` at 400/50 parameters with paragraph-aware splitting. Verified output by printing sample chunks and checking that individual reviews were preserved as coherent units (not split mid-sentence).

**Milestone 4 — Embedding and retrieval:**
Used Claude with the Retrieval Approach section and Architecture diagram as input. Asked it to implement `embed.py` loading from `documents/`, embedding with `all-MiniLM-L6-v2`, storing in ChromaDB with `source` and `url` metadata. Verified by running `query.py` on 3 test questions and checking distance scores.

**Milestone 5 — Generation and interface:**
Used Claude with the system prompt grounding requirement and Gradio layout as input. Asked it to implement `query.py` and `app.py`. Reviewed and updated the system prompt to make grounding explicit ("ONLY the information provided") rather than advisory. Added a debug panel showing retrieved chunks and distance scores to make retrieval quality visible during evaluation.
