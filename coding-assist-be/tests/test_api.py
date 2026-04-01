import os

from fastapi.testclient import TestClient

os.environ["EXECUTION_BACKEND"] = "local"

from app.main import app  # noqa: E402


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_problems():
    response = client.get("/api/v1/problems")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    assert "id" in data[0]
    assert "topics" in data[0]


def test_run_submission_accepted():
    code = """
def solve():
    n = int(input().strip())
    nums = list(map(int, input().split()))
    target = int(input().strip())
    seen = {}
    for i, value in enumerate(nums):
        needed = target - value
        if needed in seen:
            left = seen[needed]
            right = i
            print(left, right)
            return
        seen[value] = i
    print(-1)
"""
    payload = {"problem_id": "two-sum", "code": code}
    response = client.post("/api/v1/submissions/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "accepted"
    assert data["passed_count"] == data["total_count"]
    assert isinstance(data["sample_results"], list)
    assert data["hidden_passed_count"] == data["hidden_total_count"]


def test_run_submission_custom_input():
    code = """
def solve():
    text = input().strip()
    print(text.upper())
"""
    payload = {"problem_id": "two-sum", "code": code, "custom_input": "hello\n"}
    response = client.post("/api/v1/submissions/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "accepted"
    assert data["failed_case_summary"]["scope"] == "custom"
    assert data["failed_case_summary"]["actual_output"] == "HELLO"


def test_hint_shape_includes_source_and_level():
    response = client.post(
        "/api/v1/assistant/hint",
        json={
            "problem_id": "two-sum",
            "code": "def solve():\n    print(-1)",
            "latest_verdict": "wrong_answer",
            "user_question": "How should I debug this?",
            "attempt_number": 1,
            "latest_failure_summary": "sample: output mismatch",
            "coaching_mode": "balanced",
            "focus_area": "debugging",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] in {"model", "fallback"}
    assert data["hint_level"] in {"diagnosis", "next_step", "complexity"}
    assert data["next_hint_level"] in {"diagnosis", "next_step", "complexity"}
    assert 0 <= data["confidence"] <= 1
    assert data["conversation_id"]
    assert data["guided_hint"]


def test_hint_conversation_roundtrip():
    first = client.post(
        "/api/v1/assistant/hint",
        json={
            "problem_id": "two-sum",
            "code": "def solve():\n    print(-1)",
            "latest_verdict": "wrong_answer",
            "user_question": "Give me one tiny clue",
            "coaching_mode": "balanced",
        },
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]
    assert conversation_id

    second = client.post(
        "/api/v1/assistant/hint",
        json={
            "problem_id": "two-sum",
            "code": "def solve():\n    print(-1)",
            "latest_verdict": "wrong_answer",
            "user_question": "Now one more step",
            "coaching_mode": "balanced",
            "conversation_id": conversation_id,
        },
    )
    assert second.status_code == 200
    data = second.json()
    assert data["conversation_id"] == conversation_id
