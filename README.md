# VuongEdu: AI Learning Assistant

A personal learning assistant for Vietnamese high-school subjects. Students ask questions about their textbooks and get
answers with page citations, practise with generated quizzes, see which topics they are weak in, and get a study plan
that an AI agent drafts and then checks and repairs against explicit rules.

## Features

- **Textbook Q&A with citations:** hybrid retrieval (vector + BM25, fused with RRF) over the user's own PDFs; scanned
  pages are OCR'd with Gemini vision and cached.
- **Quizzes:** structured-output question generation with cross-checked answers, plus a hand-written question bank.
- **Mastery tracking:** per-topic mastery weighted by difficulty and recency, spaced repetition (SM-2) and a
  cross-grade prerequisite graph (82 topics, 103 edges).
- **Study-plan agent:** Gemini function calling with 6 tools and a diagnose → plan → critique pipeline. Code-based
  validators check 5 rules and an auto-repair step fixes violations before a plan is saved.
- **Knowledge tracing:** Deep Knowledge Tracing (LSTM) model to predict the next answer.
- **More:** essay and photo grading, classrooms for teachers, role-based access (student / teacher / admin),
  63 REST endpoints with JWT authentication.

## Results

| Evaluation | Result |
|---|---|
| Retrieval on 28 textbook questions | Hit@5 **96%**, MRR **0.88** |
| Study plans passing all rules (16 plans) | **3/16** from the LLM alone → **12/16** after auto-repair |
| Knowledge tracing, ASSISTments 2009 (AUC) | DKT **0.825** vs logistic regression 0.761 vs per-skill rate 0.620 |

Details: [`eval/`](eval/).

## Stack

FastAPI · SQLite (SQLAlchemy) · ChromaDB · Google Gemini (`google-genai`) · PyMuPDF · PyTorch · vanilla JS front end ·
Streamlit (legacy UI)

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY and a random JWT_SECRET
./start.sh --no-tunnel        # open http://localhost:8000
```

API docs (Swagger): http://localhost:8000/docs. Demo account with two weeks of data: `python -m scripts.seed_demo`,
then log in as `demo`.

**Textbooks are not included.** They are copyrighted, so upload your own PDFs in the *Documents* page, or load a whole
book by chapter with `scripts/ingest_book.py`. The knowledge-tracing dataset is also not redistributed; see
[`data/kt/README.md`](data/kt/README.md).

## Project layout

| Path | Contents |
|---|---|
| `api/` | FastAPI app, JWT auth and role checks, all endpoints |
| `app/` | RAG (ingest, OCR, retrieval), quiz, analytics, spaced repetition, agents, reflection, ML |
| `web/` | single-page web UI |
| `eval/` | retrieval, agent and knowledge-tracing evaluations |
| `scripts/` | book ingestion, demo data, tests |
| `data/` | taxonomy, prerequisite graph, question bank, trained models |

Full Vietnamese documentation: [`docs/README_vi.md`](docs/README_vi.md) and [`CAI_DAT.md`](CAI_DAT.md) (setup guide).

## Author

Built by **Phan Ngoc Vuong** ([@VuongPhan-09](https://github.com/VuongPhan-09)) as a personal project, 2026.

## License

Code: [MIT](LICENSE). Portrait images in `web/static/images/portraits/` come from Wikimedia Commons; sources are listed
in `NGUON.json`.
