import requests

BASE_URL = "http://localhost:8000"

def seed_session() -> str:
    resp = requests.post(
        f"{BASE_URL}/sessions",
        json={"proposal": "A browser extension that blocks distracting sites during a coding sprint"},
    )
    resp.raise_for_status()
    session_id = resp.json()["id"]
    print(f"Created session {session_id}")

    answers = [
        "Me and other hackathon participants who get distracted mid-sprint",
        "It should block a fixed list of sites completely during a timer, no snoozing",
    ]
    for answer in answers:
        resp = requests.post(
            f"{BASE_URL}/sessions/{session_id}/answers",
            json={"answer": answer},
        )
        resp.raise_for_status()
        print(f"Answered: {answer}")

    return session_id

def seed_criteria_and_options(session_id: str) -> None:
    criteria = {
        "speed to build": 5,
        "works without installing anything": 4,
    }
    criterion_ids = {}
    for name, weight in criteria.items():
        resp = requests.post(
            f"{BASE_URL}/sessions/{session_id}/criteria",
            json={"name": name, "weight": weight},
        )
        resp.raise_for_status()
        criterion_ids[name] = resp.json()["id"]
        print(f"Added criterion: {name} (weight {weight})")

    options = {
        "Chrome extension": {"speed to build": 4, "works without installing anything": 5},
        "Browser proxy": {"speed to build": 3, "works without installing anything": 3},
        "System-level blocker": {"speed to build": 2, "works without installing anything": 1},
    }
    for option_name, scores in options.items():
        for criterion_name, score in scores.items():
            resp = requests.post(
                f"{BASE_URL}/sessions/{session_id}/options",
                json={
                    "option_name": option_name,
                    "criterion_id": criterion_ids[criterion_name],
                    "score": score,
                },
            )
            resp.raise_for_status()
        print(f"Scored option: {option_name}")

def main() -> None:
    session_id = seed_session()
    seed_criteria_and_options(session_id)

    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/export")
    resp.raise_for_status()
    paths = resp.json()
    print(f"Exported: {paths['markdown_path']}")
    print(f"Exported: {paths['pdf_path']}")

    print(f"\nDone. Try: curl localhost:8000/sessions/{session_id}/comparison")

if __name__ == "__main__":
    main()