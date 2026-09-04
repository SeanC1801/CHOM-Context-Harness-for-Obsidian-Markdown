import uuid
import pytest
from app.llm import get_cached_or_generate, LLMError
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pathlib import Path
from app.report import build_report_data,render_markdown,render_pdf
from app.db import get_connection, init_db

app = FastAPI(title="CHOM")
PROJECT_DIR = Path(__file__).resolve().parent.parent / "Project"

class ProposalIn(BaseModel):
    proposal: str

class SessionOut(BaseModel):
    id: str
    proposal: str
    first_question: str

class AnswerIn(BaseModel):
    answer : str

class AnswerOut(BaseModel):
    next_question: str | None
    done: bool

class CriterionIn(BaseModel):
    name: str
    weight: int

class CriterionOut(BaseModel):
    id: str
    name: str
    weight: int

class OptionScoreIn(BaseModel):
    option_name: str
    criterion_id: str
    score: int

class OptionScoreOut(BaseModel):
    id: str
    option_name: str
    criterion_id: str
    score: int

class OptionalTotal(BaseModel):
    option_name: str
    total_score: int

class ComparisonOut(BaseModel):
    options: list[OptionalTotal]

class ExportOut(BaseModel):
    markdown_path: str
    pdf_path: str

@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/sessions", response_model=SessionOut)
def create_session(body: ProposalIn) -> SessionOut:
    if not body.proposal.strip():
        raise HTTPException(status_code=422, detail="proposal must not be empty")

    try: 
        session_id = str(uuid.uuid4())
        conn = get_connection()
        try:
            first_question = get_cached_or_generate(conn, body.proposal, [])
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    
        conn.execute(
            "INSERT INTO sessions (id, proposal, first_question) VALUES (?, ?, ?)",
            (session_id, body.proposal, first_question),
        )
        conn.commit()
        return SessionOut(id=session_id, proposal=body.proposal, first_question=first_question)
    finally:
        conn.close()


@app.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str) -> SessionOut:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, proposal, first_question FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    return SessionOut(id=row["id"], proposal=row["proposal"], first_question=row["first_question"])

# Identifying sessions
@app.post("/sessions/{session_id}/answers", response_model=AnswerOut)
def submit_answer(session_id: str, body: AnswerIn) -> AnswerOut:
    if not body.answer.strip():
        raise HTTPException(status_code=422, detail="answer must not be empty")
    
    conn = get_connection()
    session_row = conn.execute(
        "SELECT proposal, first_question FROM sessions WHERE id = ?", (session_id,),
    ).fetchone()
    
    if session_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="session not found")
    
    # Storing the proposal in the current question variable to indicate that we are on the first question
    current_question = session_row["first_question"]

    prior_rows = conn.execute(
        "SELECT answer FROM answers WHERE session_id = ? ORDER BY created_at", (session_id,),
    ).fetchall()
    prior_answers = [row["answer"] for row in prior_rows] + [body.answer]

    try:
        answer_id = str(uuid.uuid4())
        conn.execute(
                "INSERT INTO answers (id, session_id, question, answer) VALUES (?, ?, ?, ?)",
                (answer_id, session_id, current_question, body.answer),
            )

        if len(prior_answers) >= 5:    
            conn.commit()
            return AnswerOut(next_question=None, done=True)

        try: 
            next_question = get_cached_or_generate(conn, session_row["proposal"], prior_answers)
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        conn.execute(
            "UPDATE sessions SET first_question = ? WHERE id = ?", (next_question, session_id)
        )
        conn.commit()
        return AnswerOut(next_question=next_question, done=False)
    finally:
        conn.close()

@app.post("/sessions/{session_id}/criteria", response_model=CriterionOut)
def add_criterion(session_id: str, body: CriterionIn) -> CriterionOut:
    if not body.name.strip():
        raise HTTPException(status_code=422, detail="name must not be empty")
    
    conn = get_connection()
    try:
        session_row = conn.execute(
            "SELECT id FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session_row is None:
            raise HTTPException(status_code=404, detail="session not found")

        criterion_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO criteria (id, session_id, name, weight) VALUES (?,?,?,?)",
            (criterion_id, session_id, body.name, body.weight),
        )
        conn.commit()
        return CriterionOut(id=criterion_id, name=body.name, weight=body.weight)
    finally:
        conn.close()

@app.post("/sessions/{session_id}/options", response_model=OptionScoreOut)
def add_option_score(session_id: str, body: OptionScoreIn) -> OptionScoreOut:
    if not body.option_name.strip():
        raise HTTPException(status_code=422, detail="option_name must not be empty")
    if not 1 <= body.score <= 5:
        raise HTTPException(status_code=422, detail="score must be between 1 and 5")

    conn = get_connection()
    try:
        criterion_row = conn.execute(
            "SELECT id FROM criteria WHERE id = ? AND session_id = ?",
            (body.criterion_id, session_id),
        ).fetchone()
        if criterion_row is None:
            raise HTTPException(status_code=404, detail="criterion not found for this session")

        score_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO option_scores (id, session_id, option_name, criterion_id, score) VALUES (?, ?, ?, ?, ?)",
            (score_id, session_id, body.option_name, body.criterion_id, body.score),
        )
        conn.commit()
        return OptionScoreOut(id=score_id, option_name=body.option_name, criterion_id=body.criterion_id, score=body.score)
    finally:
        conn.close()

@app.get("/sessions/{session_id}/comparison", response_model=ComparisonOut)
def compare_options(session_id: str) -> ComparisonOut:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT option_scores.option_name AS option_name,
                SUM(option_scores.score * criteria.weight) AS total_score
            FROM option_scores
            JOIN criteria ON criteria.id = option_scores.criterion_id
            WHERE option_scores.session_id = ?
            GROUP by option_scores.option_name
            ORDER by total_score DESC
            """,
            (session_id,),
        ).fetchall()
    finally:
        conn.close()

    options = [
        OptionalTotal(
            option_name=row["option_name"],
            total_score=row["total_score"]
        ) for row in rows
    ]

    return ComparisonOut(options=options)


# Exporting to markdown files
@app.post("/sessions/{session_id}/export", response_model=ExportOut)
def export_session(session_id: str) -> ExportOut:
    conn = get_connection()
    try:
        session_row = conn.execute(
            "SELECT id FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session_row is None:
            raise HTTPException(status_code=404, detail="session not found")

        data = build_report_data(conn, session_id)
    finally:
        conn.close()

    PROJECT_DIR.mkdir(exist_ok=True)

    markdown_path = PROJECT_DIR / f"{session_id}.md"
    markdown_path.write_text(render_markdown(data))

    pdf_path = PROJECT_DIR / f"{session_id}.pdf"
    render_pdf(data, str(pdf_path))

    return ExportOut(markdown_path=str(markdown_path), pdf_path=str(pdf_path))

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(
        "app.main.get_cached_or_generate",
        lambda conn, proposal, prior_answers: "Fake generated question?"
    )

    from app.main import app
    with TestClient(app) as test_client:
        yield test_client
        