import pytest
from fastapi.testclient import TestClient

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
    
def test_create_session_returns_question(client):
    resp = client.post("/sessions", json={"proposal": "test proposal"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["proposal"] == "test proposal"
    assert body["first_question"] == "Fake generated question?"
    assert "id" in body

def test_empty_proposal_is_rejected(client):
    resp = client.post("/sessions", json={"proposal": " "})
    assert resp.status_code == 422

def test_get_nonexistent_session_returns_404(client):
    resp = client.get("/sessions/does-not-exist")
    assert resp.status_code == 404

def test_option_score_out_of_range_rejected(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]
    criterion_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "cost", "weight": 3}
    ).json()["id"]

    resp = client.post(
        f"/sessions/{session_id}/options",
        json={"option_name": "Option A", "criterion_id": criterion_id, "score": 6},
    )
    assert resp.status_code == 422

def test_option_score_with_criterion_from_another_session_rejected(client):
    session_a = client.post("/sessions", json={"proposal": "test A"}).json()["id"]
    session_b = client.post("/sessions", json={"proposal": "test B"}).json()["id"]

    criterion_id = client.post(
        f"/sessions/{session_a}/criteria", json={"name": "cost", "weight": 3}
    ).json()["id"]

    resp = client.post(
        f"/sessions/{session_b}/options",
        json={"option_name": "Option X", "criterion_id": criterion_id, "score": 3},
    )
    assert resp.status_code == 404

def test_answer_cap_stops_after_five(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]

    for i in range(4):
        resp = client.post(f"/sessions/{session_id}/answers", json={"answer": f"answer {i}"})
        assert resp.status_code == 200
        assert resp.json()["done"] is False

    resp = client.post(f"/sessions/{session_id}/answers", json={"answer": "final answer"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["done"] is True
    assert body["next_question"] is None

def test_comparison_computes_weighted_totals(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]

    cost_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "cost", "weight": 3}
    ).json()["id"]
    speed_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "speed", "weight": 5}
    ).json()["id"]

    client.post(f"/sessions/{session_id}/options", json={"option_name": "Option A", "criterion_id": cost_id, "score": 4})
    client.post(f"/sessions/{session_id}/options", json={"option_name": "Option A", "criterion_id": speed_id, "score": 2})
    client.post(f"/sessions/{session_id}/options", json={"option_name": "Option B", "criterion_id": cost_id, "score": 2})
    client.post(f"/sessions/{session_id}/options", json={"option_name": "Option B", "criterion_id": speed_id, "score": 5})

    resp = client.get(f"/sessions/{session_id}/comparison")
    assert resp.status_code == 200
    options = {opt["option_name"]: opt["total_score"] for opt in resp.json()["options"]}
    assert options["Option A"] == 22
    assert options["Option B"] == 31

def test_duplicate_score_updates_in_place(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]
    criterion_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "cost", "weight": 3}
    ).json()["id"]

    first = client.post(
        f"/sessions/{session_id}/options",
        json={"option_name": "Option A", "criterion_id": criterion_id, "score": 4},
    ).json()
    second = client.post(
        f"/sessions/{session_id}/options",
        json={"option_name": "Option A", "criterion_id": criterion_id, "score": 2},
    ).json()

    assert first["id"] == second["id"]
    assert second["score"] == 2

    comparison = client.get(f"/sessions/{session_id}/comparison").json()
    assert comparison["options"] == [{"option_name": "Option A", "total_score": 6}]

def test_incomplete_option_excluded_from_comparison(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]
    cost_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "cost", "weight": 3}
    ).json()["id"]
    speed_id = client.post(
        f"/sessions/{session_id}/criteria", json={"name": "speed", "weight": 5}
    ).json()["id"]

    client.post(f"/sessions/{session_id}/options", json={"option_name": "Complete", "criterion_id": cost_id, "score": 1})
    client.post(f"/sessions/{session_id}/options", json={"option_name": "Complete", "criterion_id": speed_id, "score": 1})
    client.post(f"/sessions/{session_id}/options", json={"option_name": "Incomplete", "criterion_id": cost_id, "score": 5})

    comparison = client.get(f"/sessions/{session_id}/comparison").json()
    names = [opt["option_name"] for opt in comparison["options"]]
    assert names == ["Complete"]

def test_criterion_weight_out_of_range_rejected(client):
    session_id = client.post("/sessions", json={"proposal": "test"}).json()["id"]
    resp = client.post(f"/sessions/{session_id}/criteria", json={"name": "cost", "weight": 0})
    assert resp.status_code == 422