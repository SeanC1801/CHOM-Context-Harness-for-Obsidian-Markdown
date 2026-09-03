# CHOM — Context Harness for Obsidian Markdown

## The problem

Hackathon participants often begin with scattered ideas, incomplete assumptions, and competing technical directions. Turning those thoughts into a focused project plan usually takes hours of unstructured research, back-and-forth discussion, and rewriting. The result is often a weakly scoped project with no clear record of why its technical choices were made.

## Who has this problem

Individual hackathon participants and small teams who need to move from an early idea to a buildable project direction quickly, especially when time, skills, cost, accessibility, and reliability must be balanced.

## The 10x claim

CHOM aims to help a participant turn a rough hackathon idea into a user-approved, technically justified project brief in about 15 minutes instead of several hours. The claim will be tested by timing a structured CHOM session against a manual planning session using the same sample idea.

## Core solution

CHOM is an AI-guided deliberation tool, not an automatic project chooser. It asks one focused question at a time, captures the participant's answers and priorities, identifies unresolved trade-offs, and presents a small set of system options. The participant assigns importance to criteria, weighs pros and cons, selects the final direction, and approves the resulting documentation.

CHOM then creates editable, Obsidian-compatible Markdown files in a `Project/` folder and a concise PDF decision report. Generated documentation is based on user-confirmed answers; the AI does not invent final decisions.

## Core features — v1 only

1. Create an idea session and save the initial concept.
2. Run a bounded, AI-generated question flow about the problem, users, constraints, and success criteria.
3. Let the participant set criteria weights and record pros and cons.
4. Compare 2–3 architecture options through transparent, deterministic scoring and user-facing trade-offs.
5. Generate approved Obsidian Markdown project files and a PDF decision report.

## Capstone concepts

| Concept | Where it lives in CHOM |
| --- | --- |
| API endpoints | FastAPI endpoints create sessions, receive answers, return the next question, score options, and export artifacts. |
| Database | SQLite persists sessions, answers, criteria, options, decisions, and artifact history. |
| LLM integration | A narrow endpoint generates the next focused question and validates structured AI output before it is shown. |
| Caching logic | A hash of the session state reuses an unchanged generated question or assessment instead of repeating an LLM call. |
| Reporting | CHOM creates a concise PDF decision report alongside its Markdown project brief. |

## Explicit non-goal

CHOM will not build the participant's application, autonomously choose an architecture, browse or scrape the web, manage team collaboration, or automate third-party tools. It guides thinking and records decisions; the participant remains in control.

## Initial technical direction

One FastAPI application with SQLite, Pydantic validation, a single LLM-provider adapter, template-based Markdown generation, PDF reporting, and pytest. The initial delivery will run locally with documented commands and seeded demo data; Docker and external workflow tools are out of scope for v1.
