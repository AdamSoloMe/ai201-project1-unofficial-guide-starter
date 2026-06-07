# The Unofficial Guide — Project 1


## Domain

CUNY Queens College Computer Science professor reviews sourced from Rate My Professors. Queens College course catalogs describe what a course covers, but say nothing about what it is actually like to take it — exam difficulty, grading fairness, office hour responsiveness, or how clearly the professor explains concepts. A student choosing between sections of CS111 or CS320 has no official resource for that kind of peer knowledge. Rate My Professors aggregates it, but requires manually visiting each professor's page and reading through reviews. This RAG system makes it searchable: students can ask plain-language questions like "Is Ryba a good professor?" or "Which CS professor is the hardest?" and get grounded, cited answers drawn from real student reviews.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Jerry Waxman | RMP professor page (312 reviews) | https://www.ratemyprofessors.com/professor/287312 |
| 2 | Alex Ryba | RMP professor page (150 reviews) | https://www.ratemyprofessors.com/professor/44623 |
| 3 | Simina Fluture | RMP professor page (276 reviews) | https://www.ratemyprofessors.com/professor/513427 |
| 4 | John Svadlenka | RMP professor page (164 reviews) | https://www.ratemyprofessors.com/professor/2485140 |
| 5 | Kent Boklan | RMP professor page (149 reviews) | https://www.ratemyprofessors.com/professor/629756 |
| 6 | Anne Smith-Thompson | RMP professor page (121 reviews) | https://www.ratemyprofessors.com/professor/352320 |
| 7 | Matthew Fried | RMP professor page (91 reviews) | https://www.ratemyprofessors.com/professor/1822595 |
| 8 | Md Mahbubur Rahman | RMP professor page (87 reviews) | https://www.ratemyprofessors.com/professor/2649371 |
| 9 | Robert Goldberg | RMP professor page (86 reviews) | https://www.ratemyprofessors.com/professor/446485 |
| 10 | Jackson Yeh | RMP professor page (76 reviews) | https://www.ratemyprofessors.com/professor/1082596 |
| 11 | Paul Cesaretti | RMP professor page (59 reviews) | https://www.ratemyprofessors.com/professor/2354095 |
| 12 | Mayank Goswami | RMP professor page (44 reviews) | https://www.ratemyprofessors.com/professor/2195317 |
| 13 | Russell Gomes | RMP professor page (16 reviews) | https://www.ratemyprofessors.com/professor/2913678 |
| 14 | Delaram Kahrobaei | RMP professor page (23 reviews) | https://www.ratemyprofessors.com/professor/2870283 |
| 15 | Themistokles Bournias | RMP professor page (5 reviews) | https://www.ratemyprofessors.com/professor/3058898 |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**

Rate My Professors reviews are short — typically 50–250 characters each. A 600-character chunk (appropriate for long-form guides or wiki articles) would merge 3–5 unrelated reviews into one embedding, diluting the semantic signal. The embedding would represent a blend of opinions rather than a specific viewpoint, making it harder to retrieve the right chunk for a targeted query like "what do students say about Ryba's grading?"

A 400-character chunk fits 1–3 reviews naturally. The chunker is paragraph-aware — it merges content until the 400-character limit is reached, then starts a new chunk carrying a 50-character tail of overlap. The 50-character overlap is intentionally small: individual reviews are self-contained, so there is little need to carry context from one review to the next. The overlap mainly guards against splitting a single longer review mid-sentence.

Each document opens with a structured professor metadata header (name, department, overall rating, difficulty, would-take-again percentage). This header is preserved in the first chunk of each professor's document, allowing retrieval queries like "who is the highest-rated professor?" to match on structured metadata in addition to review text.

**Final chunk count:** 525 chunks across 15 documents

---

## Sample Chunks

**Chunk 1 — Source: Alex_Ryba**
> "Professor: Alex Ryba\nDepartment: Computer Science\nSchool: CUNY Queens College (Queens, NY)\nOverall Rating: 4.5/5.0\nDifficulty: 2.8/5.0\nWould Take Again: 88%\nNumber of Ratings: 150"

**Chunk 2 — Source: Alex_Ryba**
> "Course: CS101 | Date: 2023-04-10 | Rating: 5/5 | Difficulty: 2/5 | Grade: A | Would take again: Yes\n\"Alex Ryba is amazing. Lectures are clear, organized, and he uses real world examples to make concepts click. He posts recorded lectures online which is a lifesaver.\""

**Chunk 3 — Source: Kent_Boklan**
> "Course: CS320 | Date: 2022-11-15 | Rating: 1/5 | Difficulty: 5/5 | Grade: C | Would take again: No\n\"Extremely hard grader. The exams have nothing to do with the homework and he gives very little partial credit. Would not recommend unless you already know the material.\""

**Chunk 4 — Source: Jerry_Waxman**
> "Professor: Jerry Waxman\nDepartment: Computer Science\nSchool: CUNY Queens College (Queens, NY)\nOverall Rating: 3.4/5.0\nDifficulty: 3.1/5.0\nWould Take Again: 55%\nNumber of Ratings: 312"

**Chunk 5 — Source: Matthew_Fried**
> "Course: CS211 | Date: 2023-09-01 | Rating: 5/5 | Difficulty: 3/5 | Grade: A | Would take again: Yes\n\"Professor Fried is one of the best CS professors at Queens. He explains things step by step and is always willing to help during office hours.\""

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Production tradeoff reflection:**

`all-MiniLM-L6-v2` was chosen because it runs entirely locally — no API key, no rate limits, and no cost per query. It produces 384-dimensional embeddings quickly and is well-suited for a small corpus of short review documents.

For a production deployment serving students at scale, the key tradeoffs to weigh:

- **Context length:** MiniLM is capped at 256 tokens. Short reviews fit well within this limit, so truncation is rarely an issue for this corpus. For longer documents (course syllabi, housing guides), a higher-limit model would matter more.
- **Domain specificity:** MiniLM is trained on general web text. Course codes like "CS31" or "CS111" are treated as character sequences rather than semantic identifiers. A model fine-tuned on educational or review-style text would likely improve retrieval precision for course-specific queries.
- **Accuracy vs. cost:** OpenAI's `text-embedding-3-small` consistently outperforms MiniLM on retrieval benchmarks, and would reduce the retrieval failures observed for vague comparative queries (e.g., "which professor gives the most helpful feedback"). The cost per query is low, making it viable for production.
- **Multilingual support:** Queens College has one of the most diverse student populations in the US. A multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would allow queries in Spanish, Chinese, Korean, or other languages to retrieve English-language reviews.

---

## Grounded Generation

**System prompt grounding instruction:**

```
You are a helpful assistant for students at CUNY Queens College looking for honest,
student-sourced information about Computer Science professors. Answer the user's
question using ONLY the information provided in the retrieved Rate My Professors
reviews below. Do not use any outside knowledge.

If the excerpts do not contain enough information to answer the question,
respond with: "I don't have enough information in my documents to answer that."

Always cite which professor's page(s) your answer draws from at the end of your
response, like this: [Source: ProfessorName]
```

The key grounding mechanism is "ONLY the information provided in the retrieved Rate My Professors reviews" — this is an explicit prohibition rather than a soft suggestion. The instruction also mandates a fallback response when documents are insufficient, preventing the model from filling gaps with general knowledge about professors it might have in its training data.

**How source attribution is surfaced in the response:**

Source attribution is enforced two ways: (1) the system prompt instructs the LLM to include `[Source: ProfessorName]` at the end of its response, and (2) `query.py` programmatically extracts the source names of all retrieved chunks and displays them in a separate "Sources" field in the UI — so citations are always visible to the user even if the model omits them from the answer text.

---

## Retrieval Test Results

**Query 1:** "Which CS professor at Queens College is the most highly rated by students?"

Top returned chunks:
- [distance: 0.58, Source: Delaram_Kahrobaei] Professor metadata header — Overall Rating: 3.9/5.0
- [distance: 0.63, Source: Kent_Boklan] Professor metadata header — Overall Rating: 2.5/5.0
- [distance: 0.67, Source: Matthew_Fried] Professor metadata header — Overall Rating: 4.0/5.0

Why these chunks are relevant: The results are professor metadata headers containing structured rating numbers, which is the right content for a ratings-comparison query. However, Alex Ryba (4.5/5.0, the highest rated in the corpus) was not in the top retrieved chunks — the embedding model doesn't rank by numeric value, only by semantic similarity to the query string. This is the documented failure case.

---

**Query 2:** "What do students say about Alex Ryba's teaching style and difficulty?"

Top returned chunks:
- [distance: 0.42, Source: Alex_Ryba] Review text: "Alex Ryba is amazing. Lectures are clear, organized, and he uses real world examples to make concepts click. He posts recorded lectures online which is a lifesaver."
- [distance: 0.48, Source: Alex_Ryba] Additional Ryba review discussing teaching clarity and difficulty
- [distance: 0.71, Source: Robert_Goldberg] Loosely related review about a different professor's teaching style

Why these chunks are relevant: The top two results correctly pull from the Alex_Ryba document with low distance scores (0.42, 0.48), indicating strong semantic alignment. Both contain direct student opinions about teaching style and course difficulty. The third result is from a different professor but shares vocabulary about teaching style — typical behavior when the query is partially generic.

---

**Query 3:** "Is Jerry Waxman a good professor?"

Top returned chunks:
- [distance: 0.51, Source: Jerry_Waxman] Review mentioning Waxman's lecturing style
- [distance: 0.55, Source: Jerry_Waxman] Additional Waxman review with mixed feedback
- [distance: 0.74, Source: Russell_Gomes] Off-topic result from a different professor

Why these chunks are relevant: The top two results correctly surface Waxman reviews with moderate distance scores. The mixed sentiment in the retrieved reviews (some positive, some critical) accurately reflects his 3.4/5.0 average rating.

---

## Example Responses

**Example 1 — Grounded response with citation:**

> **Q:** What do students say about Alex Ryba's teaching style and difficulty?
>
> **A:** Students describe Alex Ryba's teaching style as clear, organized, and easy to digest, with many using "real world" examples to solidify concepts. He is also praised for providing practice problems, recording lectures, and posting them online. The difficulty of his class is generally rated as 2–3 out of 5, with students finding the workload manageable if you keep up with the material.
>
> [Source: Alex_Ryba]
>
> **Sources:** Alex_Ryba, Robert_Goldberg

---

**Example 2 — Grounded response with citation:**

> **Q:** Which Queens College CS professor is easiest and which is hardest?
>
> **A:** Based on the provided excerpts, Professor Jerry Waxman has the lowest difficulty rating with an average of 3.1/5.0. On the other hand, Professor Kent Boklan has the highest difficulty rating with an average of 4.5/5.0.
>
> [Source: Kent_Boklan, Jerry_Waxman]
>
> **Sources:** Delaram_Kahrobaei, Kent_Boklan, Robert_Goldberg, Paul_Cesaretti, Jerry_Waxman

---

**Example 3 — Out-of-scope refusal:**

> **Q:** Who wrote the Harry Potter series?
>
> **A:** I don't have enough information in my documents to answer that. [No relevant source]
>
> **Sources:** *(none)*

---

## Query Interface

The interface is a Gradio web app launched with `python app.py` and accessible at `http://localhost:7860`.

**Input fields:**
- **Your question** — a text box where the user types a plain-language question about Queens College CS professors.

**Output fields:**
- **Answer** — the grounded response generated by `llama-3.3-70b-versatile` via Groq, always ending with professor source citations.
- **Sources** — the list of professor pages retrieved and used as context.
- **Retrieved chunks (debug)** — the raw text of the top-5 retrieved chunks with distance scores, so users can see exactly what the model was given.

Example interaction:
```
Q: Is Jerry Waxman a good professor for CS courses?

A: Based on the provided excerpts, Jerry Waxman has a mixed reputation. One student
   review mentions that he is a "very good lecturer" and helps students understand
   the material well. However, other reviews cite difficulty keeping up with the
   pace of his lectures and limited availability outside of class. His overall
   rating is 3.4/5.0 with 312 reviews.
   [Source: Jerry_Waxman]

Sources:
• Jerry_Waxman
• Paul_Cesaretti
• Russell_Gomes
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which CS professor at Queens College is the most highly rated by students? | Alex Ryba (4.5/5.0, 150 ratings) — system should name a specific professor with rating data | Named Matthew Fried (4.0) as highest rated — missed Ryba (4.5) who wasn't surfaced in top retrieved chunks | Partially relevant | Partially accurate |
| 2 | What do students say about Alex Ryba's teaching style and difficulty? | Clear, organized, uses real-world examples; records lectures; difficulty rated 2–3/5 | Correctly described teaching style as clear and organized; cited recorded lectures and real-world examples; correctly noted low difficulty | Relevant | Accurate |
| 3 | Is Jerry Waxman a good professor for CS courses? | Mixed — some praise his lecturing, others find him hard to follow; 3.4/5.0 overall | Correctly conveyed mixed reputation; cited both positive and critical reviews; referenced 3.4 rating | Relevant | Accurate |
| 4 | What do students complain about most in Queens College CS courses? | High difficulty with unfair grading (Boklan cited); disorganized lectures; heavy workloads | Correctly identified Boklan's high difficulty and unfair grading as top complaints; mentioned 5/5 difficulty reviews | Relevant | Accurate |
| 5 | Which Queens College CS professor is easiest and which is hardest? | Easiest: Ryba or Fried (low difficulty scores); Hardest: Boklan (4.5/5.0 difficulty) | Named Waxman as easiest (3.1/5.0) and Boklan as hardest (4.5/5.0) — Waxman answer plausible but not the best evidence; Boklan correct | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Which CS professor at Queens College is the most highly rated by students?"

**What the system returned:** Named Matthew Fried (4.0/5.0) as the highest-rated professor. The correct answer, based on the documents, is Alex Ryba (4.5/5.0, 150 ratings).

**Root cause (tied to a specific pipeline stage):** The failure is in the retrieval stage. The query "most highly rated" retrieves professor metadata headers based on semantic similarity — but "most highly rated" doesn't map cleanly onto any specific phrase in the metadata headers. The retrieved headers happened to include Delaram Kahrobaei, Kent Boklan, and Matthew Fried, but Alex Ryba's header (which contains "4.5/5.0") was not ranked in the top 5. The embedding model treats rating numbers in each header as equivalent tokens; it has no way to compare across documents to find the maximum. This is a fundamental limitation of vector similarity search for comparative/superlative queries — semantic similarity finds documents that are *about* ratings, not the document that contains the *highest* rating.

**What you would change to fix it:** For comparative queries like "highest rated," a metadata filtering approach would work better than pure semantic search. The `embed.py` pipeline already stores `avgRating` as part of the source document — adding it as a numeric ChromaDB metadata field would allow queries like "retrieve all chunks, sort by avgRating descending, take top 3" to directly answer this kind of question without relying on embedding similarity.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The evaluation plan section forced specific, verifiable test questions to be written before any code was written. This directly influenced chunking decisions — question 2 ("what do students say about Alex Ryba's teaching style?") requires that Ryba's reviews be retrievable as distinct, coherent chunks. Knowing this question existed before chunking made it clear that reviews should not be merged into large undifferentiated blocks. The spec made the downstream consequences of chunking decisions concrete rather than abstract.

**One way your implementation diverged from the spec, and why:**

The spec assumed Rate My Professors could be scraped with standard HTTP requests. In practice, the website returns 403 Forbidden to Python's `requests` library. The implementation switched to the RMP GraphQL API (`https://www.ratemyprofessors.com/graphql`) instead of HTML scraping — this produced cleaner structured data (JSON) that required no BeautifulSoup HTML parsing at all, and the `mwparserfromhell` library that had been added to `requirements.txt` for wiki parsing was no longer needed. The spec's AI Tool Plan section was updated to reflect this change.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents table and Chunking Strategy section from planning.md, plus a description of the RMP GraphQL API structure (the endpoint, the auth header, and the fact that the school and department searches require object inputs rather than plain strings).
- *What it produced:* An `ingest.py` that made the correct API calls and formatted each professor page as a structured text document with a metadata header followed by individual reviews.
- *What I changed or overrode:* The initial generated code used `departmentFilter` as the field name in `TeacherSearchQuery`, which caused a GraphQL schema error. After probing the API's introspection endpoint, the correct field name (`departmentID`) was identified, and the ID needed to be base64-encoded as `"Department-{numeric_id}"`. The generated code was updated to fetch department IDs from the school node and encode them correctly.

**Instance 2**

- *What I gave the AI:* The Retrieval Approach section, the Architecture diagram, and the grounding requirement ("answer using ONLY retrieved documents, decline if insufficient, cite sources").
- *What it produced:* `query.py` with lazy-loaded singletons (model, ChromaDB collection, Groq client) and `app.py` with a two-column Gradio layout.
- *What I changed or overrode:* The generated system prompt said "Please answer based on the provided documents" — changed to "Answer the user's question using ONLY the information provided" to make the grounding constraint explicit rather than advisory. The domain-specific framing ("helpful assistant for students at CUNY Queens College looking for information about CS professors") was also added to focus the model's persona on the correct use case.
