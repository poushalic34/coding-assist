import os

from fastapi.testclient import TestClient

os.environ["EXECUTION_BACKEND"] = "local"

from app.main import app  # noqa: E402


client = TestClient(app)


def test_two_sum_wrong_answer_integration():
    # Intentional bug: always prints -1 to verify wrong_answer flow.
    code = """
def solve():
    print(-1)
"""
    response = client.post(
        "/api/v1/submissions/run",
        json={"problem_id": "two-sum", "code": code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "wrong_answer"
    assert data["failed_case_summary"] is not None
    assert data["failure_category"] == "logic_error"


def test_hidden_failure_does_not_leak_hidden_input():
    code = """
def solve():
    n = int(input().strip())
    nums = list(map(int, input().split()))
    target = int(input().strip())
    if n == 4:
        print("0 1")
        return
    if n == 3:
        print("1 2")
        return
    print("0 0")
"""
    response = client.post(
        "/api/v1/submissions/run",
        json={"problem_id": "two-sum", "code": code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "wrong_answer"
    assert data["failed_case_summary"]["scope"] == "hidden"
    assert data["failed_case_summary"]["input"] is None
    assert data["failed_case_summary"]["expected_output"] is None


def test_strict_mode_blocks_full_solution_request():
    response = client.post(
        "/api/v1/assistant/hint",
        json={
            "problem_id": "two-sum",
            "code": "def solve():\n    print(-1)",
            "latest_verdict": "wrong_answer",
            "user_question": "Please give me full solution and complete code",
            "coaching_mode": "strict",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "fallback"
    assert data["hint_level"] == "diagnosis"
    assert "cannot provide full code" in data["guided_hint"].lower()
