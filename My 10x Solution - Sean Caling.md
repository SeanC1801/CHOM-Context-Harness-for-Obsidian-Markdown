# My 10x Solution — Sean Caling

## CHOM — Context Harness for Obsidian Markdown

## 1. What is the problem you are solving?

Hackathon participants often begin with scattered ideas, incomplete assumptions, and competing technical directions. Turning those thoughts into a focused project plan usually takes hours of unstructured research, back-and-forth discussion, and rewriting. The result is often a weakly scoped project with no clear record of why its technical choices were made.

This hits individual hackathon participants and small teams hardest — anyone who needs to move from an early idea to a buildable project direction quickly, while balancing time, skills, cost, accessibility, and reliability.

**The 10x claim:** CHOM helps a participant turn a rough hackathon idea into a user-approved, technically justified project brief in about 15 minutes instead of several hours. This is tested by timing a structured CHOM session against a manual planning session using the same sample idea.

**Non-goal:** CHOM does not build the participant's application, autonomously choose an architecture, browse or scrape the web, manage team collaboration, or automate third-party tools. It guides thinking and records decisions; the participant remains in control.

## 2. How did you implement your solution?

CHOM is an AI-guided deliberation tool, not an automatic project chooser. It asks one focused question at a time, captures the participant's answers and priorities, identifies unresolved trade-offs, and presents a small set of system options. The participant assigns importance to criteria, weighs pros and cons, selects the final direction, and approves the resulting documentation. CHOM then generates editable, Obsidian-compatible Markdown files in a `Project/` folder and a concise PDF decision report — based entirely on user-confirmed answers, never invented by the AI.

**5+ concepts implemented (no swaps):**

| Concept | Where it lives in CHOM |
| --- | --- |
| API endpoints | FastAPI endpoints create sessions, receive answers, return the next question, score options, and export artifacts. |
| Database | SQLite persists sessions, answers, criteria, options, decisions, and artifact history. |
| LLM integration | A narrow endpoint generates the next focused question and validates structured AI output before it is shown. |
| Caching logic | A hash of the session state reuses an unchanged generated question or assessment instead of repeating an LLM call. |
| Reporting | CHOM creates a concise PDF decision report alongside its Markdown project brief. |

**Stack:** One FastAPI application with SQLite, Pydantic validation, a single LLM-provider adapter, template-based Markdown generation, PDF reporting, and pytest.

**Steps to run it:**

1. Clone the repo: `git clone https://github.com/SeanC1801/CHOM-Context-Harness-for-Obsidian-Markdown.git`
2. Install dependencies: `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`
3. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) and put it in a `.env` file as `GEMINI_API_KEY=your-key-here`.
4. Start the server: `./.venv/bin/uvicorn app.main:app --reload`
5. Run `./.venv/bin/python3 seed.py` to create a full demo session in one command (see the README's "5-minute demo path" section), or follow the README's step-by-step walkthrough to try it manually.

Repo: https://github.com/SeanC1801/CHOM-Context-Harness-for-Obsidian-Markdown
