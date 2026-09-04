import os
import hashlib
from dotenv import load_dotenv
from google import genai

load_dotenv()

class LLMError(Exception):
    pass

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_next_question(proposal: str, prior_answers: list[str]) -> str:
    history = "\n".join(f"- {a}" for a in prior_answers)
    prompt = (
        "You are helping a hackathon participant refine their project idea. "
        "Ask exactly one focused, specific question that helps them clarify "
        "the problem, the user, constraints, or success criteria. "
        "Do not answer your own questions. Return only the question, nothing else.\n\n"
        f"Original proposal: {proposal}\n\n"
        f"Answers so far:\n{history if history else '(none yet)'}"
    )

    try:
        response = _client.models.generate_content(model="gemini-3.6-flash", contents=prompt,)
        raw_text = response.text
    except Exception as exc:
        raise LLMError(f"Gemini request failed: {exc}") from exc

    question = (raw_text or "").strip()

    if not question:
        raise LLMError("Gemini returned an empty question")
    if len(question) > 300:
        raise LLMError("LLM returned a question that is too long")
    if not question.endswith("?"):
        raise LLMError("LLM response was not a single question")
    return question

def _hash_state(proposal: str, prior_answers: list[str]) -> str:
    raw = proposal + "|" + "|".join(prior_answers)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def get_cached_or_generate(conn, proposal: str, prior_answers: list[str]) -> str:
    state_hash = _hash_state(proposal, prior_answers)

    row = conn.execute(
        "SELECT question FROM question_cache WHERE state_hash = ?", (state_hash,)
    ).fetchone()

    if row is not None:
        return row["question"]

    question = generate_next_question(proposal, prior_answers)

    conn.execute(
        "INSERT INTO question_cache (state_hash, question) VALUES (?,?)", (state_hash, question),
    )
    conn.commit()
    return question