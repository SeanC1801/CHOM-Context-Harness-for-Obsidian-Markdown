import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import get_connection, init_db

app = FastAPI(title="CHOM")

FIRST_QUESTION = "What problem are you trying to solve, and who has that problem?"


class ProposalIn(BaseModel):
    proposal: str


class SessionOut(BaseModel):
    id: str
    proposal: str
    first_question: str


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/sessions", response_model=SessionOut)
def create_session(body: ProposalIn) -> SessionOut:
    if not body.proposal.strip():
        raise HTTPException(status_code=422, detail="proposal must not be empty")

    session_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (id, proposal, first_question) VALUES (?, ?, ?)",
        (session_id, body.proposal, FIRST_QUESTION),
    )
    conn.commit()
    conn.close()

    return SessionOut(id=session_id, proposal=body.proposal, first_question=FIRST_QUESTION)


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
