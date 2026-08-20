"""Tests for mock test generation, scoring, and mistake logging — the
core adaptive-learning logic of the app."""
import io


def _upload_document(client, headers, monkeypatch):
    monkeypatch.setattr(
        "app.routers.upload.pdf_processor.extract_pages",
        lambda path: [(1, "Graph theory content about vertices and edges.")],
    )
    resp = client.post(
        "/documents/upload",
        files={"file": ("graphs.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        data={"subject": "Graph Theory"},
        headers=headers,
    )
    return resp.json()["id"]


FAKE_QUESTIONS = [
    {"question": "What is a vertex?", "options": ["A node", "An edge", "A path", "A cycle"],
     "correct_index": 0, "topic": "Basics", "source": "Page 1"},
    {"question": "Sum of degrees equals?", "options": ["e", "2e", "e/2", "v"],
     "correct_index": 1, "topic": "Handshaking Theorem", "source": "Page 3"},
]


def test_generate_mock_test(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.mocktest.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3500: FAKE_QUESTIONS,
    )

    resp = client.post(
        "/mocktest/generate",
        json={"document_id": doc_id, "difficulty": "medium", "num_questions": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["questions"]) == 2
    assert body["difficulty"] == "medium"


def test_submit_perfect_score(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.mocktest.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3500: FAKE_QUESTIONS,
    )
    test = client.post(
        "/mocktest/generate",
        json={"document_id": doc_id, "difficulty": "medium", "num_questions": 2},
        headers=headers,
    ).json()

    # answers matching correct_index for both questions
    resp = client.post(
        "/mocktest/submit",
        json={"mock_test_id": test["id"], "answers": [0, 1]},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["score_pct"] == 100.0
    assert body["mistakes_logged"] == 0


def test_submit_logs_mistakes_for_wrong_answers(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.mocktest.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3500: FAKE_QUESTIONS,
    )
    test = client.post(
        "/mocktest/generate",
        json={"document_id": doc_id, "difficulty": "medium", "num_questions": 2},
        headers=headers,
    ).json()

    # both answers wrong
    resp = client.post(
        "/mocktest/submit",
        json={"mock_test_id": test["id"], "answers": [1, 0]},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["score_pct"] == 0.0
    assert body["mistakes_logged"] == 2

    mistakes = client.get("/mistakes/", headers=headers).json()
    assert len(mistakes) == 2
    topics = {m["topic"] for m in mistakes}
    assert topics == {"Basics", "Handshaking Theorem"}


def test_submit_rejects_mismatched_answer_count(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.mocktest.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3500: FAKE_QUESTIONS,
    )
    test = client.post(
        "/mocktest/generate",
        json={"document_id": doc_id, "difficulty": "medium", "num_questions": 2},
        headers=headers,
    ).json()

    # only 1 answer submitted for a 2-question test
    resp = client.post(
        "/mocktest/submit",
        json={"mock_test_id": test["id"], "answers": [0]},
        headers=headers,
    )
    assert resp.status_code == 400
