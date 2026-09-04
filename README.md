# CHOM — Context Harness for Obsidian Markdown

> An AI-guided proposal-questioning and reflection workflow for hackathon participants.

## Status

**Walking skeleton.** `POST /sessions` persists a proposal to SQLite and returns one fixed question; `GET /sessions/{id}` reads it back. No question flow, weighting, comparison, or artifact generation yet — those land in later milestones.

## Running it

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn app.main:app --reload
```

Then:

```bash
curl -X POST localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"proposal": "A tool that reminds hackers to sleep"}'
```

The response includes a session `id` and the first question. `GET /sessions/{id}` returns the same session — data survives an app restart (`chom.db`, git-ignored).

## The problem

Hackathon participants often start with an interesting idea but lack a clear problem statement, scope, technical direction, or record of why a decision was made. Unstructured planning can consume hours and still produce a project that is too broad to finish.

## What CHOM does

CHOM begins when a participant submits a project proposal in their own words. It then asks focused, bounded questions that help the participant examine assumptions, clarify constraints, identify trade-offs, and reflect on what matters most.

CHOM does **not** give a definitive answer or select an architecture for the participant. It helps them compare a small number of options against criteria they have weighted themselves, then documents their approved decision in Obsidian-compatible Markdown and a concise PDF reflection report.

```text
Project proposal
  → focused questions
  → participant reflections and criteria weights
  → transparent option comparison
  → participant selects a direction
  → Markdown project folder + PDF reflection report
```

## Who it is for

- Individual hackathon participants.
- Small hackathon teams deciding what to build.
- Students and early-stage builders who want a durable record of their project reasoning.

## Version 1 scope

1. Create and resume a proposal session.
2. Save a participant's initial proposal and answers.
3. Generate a bounded AI question flow about the problem, users, constraints, success criteria, and skills.
4. Let the participant weight criteria and record pros and cons.
5. Compare two or three options with transparent, deterministic scoring.
6. Generate approved Markdown files in a `Project/` folder and a PDF reflection report.

## Non-negotiables

- The participant makes the final decision.
- The LLM has one narrow role: ask the next focused question and provide reflective option notes.
- AI output must be validated before it is shown.
- Final artifacts are based on user-confirmed answers and selections.
- Scores must be traceable to participant-defined criteria and weights.
- The application must remain simple to run locally.

## Out of scope for v1

- Building the participant's application.
- Autonomous architecture selection or unrestricted agents.
- Web scraping, RAG, vector databases, or third-party workflow automation.
- Docker as a requirement, n8n, team collaboration features, or external syncing.

## Planned technical approach

- **API:** FastAPI
- **Persistence:** SQLite
- **Validation:** Pydantic
- **AI:** one LLM-provider adapter with structured responses
- **Caching:** session-state hashes for unchanged questions or assessments
- **Artifacts:** template-based Markdown plus PDF reporting
- **Testing:** pytest with seeded demo sessions

## FlyRank capstone concepts

| Concept | CHOM implementation |
| --- | --- |
| API endpoints | [app/main.py](app/main.py) — create sessions, receive answers, request the next question, compare options, and export artifacts. |
| Database | [app/db.py](app/db.py) — SQLite persistence for proposal sessions, answers, weights, options, decisions, and artifact history. |
| LLM integration | Generate one focused next question and reflective option notes through validated structured output. |
| Caching logic | Reuse an unchanged generated question or assessment when the session state has not changed. |
| Reporting | Create a PDF reflection report alongside Obsidian-compatible Markdown files. |

## 10x claim

CHOM aims to help a participant turn an initial hackathon proposal into a user-refined, technically reasoned project brief in about **15 minutes**, rather than several hours of unstructured planning. This claim will be tested using the same sample idea in both workflows.

## Project documents

- [One-page capstone brief](CHOM_One_Pager.md)
- [Project proposal](CHOM_Project_Proposal_v1.0.docx)

## Planned build order

1. ✅ Walking skeleton: create a proposal session, persist it, and return one question.
2. Guided question flow and structured answer storage.
3. Criteria weighting and deterministic option comparison.
4. Markdown and PDF artifact generation.
5. Caching, validation, tests, seeded demo data, and runnable setup instructions.

## Security and data handling

No secrets belong in the repository. API keys and configuration will be supplied through environment variables and excluded through `.gitignore`. Demo data will be seeded and will not use other people's personal data.

## License

License to be selected before public release.
