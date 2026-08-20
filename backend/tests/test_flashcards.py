"""Tests for flashcard generation and spaced-repetition review logic.
Mocks the LLM call — these tests verify OUR scheduling logic, not
whether Groq/Anthropic can write good flashcards."""
import io


def _upload_document(client, headers, monkeypatch):
    monkeypatch.setattr(
        "app.routers.upload.pdf_processor.extract_pages",
        lambda path: [(1, "A binary search tree keeps left < node < right.")],
    )
    resp = client.post(
        "/documents/upload",
        files={"file": ("dsa.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        data={"subject": "DSA"},
        headers=headers,
    )
    return resp.json()["id"]


def test_generate_flashcards_creates_cards(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)

    monkeypatch.setattr(
        "app.routers.flashcards.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3000: [
            {"question": "What is a BST?", "answer": "A tree with ordered children.", "difficulty": "easy"},
            {"question": "BST search time?", "answer": "O(log n) if balanced.", "difficulty": "medium"},
        ],
    )

    resp = client.post("/flashcards/generate", json={"document_id": doc_id, "count": 2}, headers=headers)
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) == 2
    assert cards[0]["question"] == "What is a BST?"
    assert cards[0]["retention"] == 0.5  # starts neutral


def test_review_increases_retention_on_correct_answer(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.flashcards.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3000: [
            {"question": "Q1", "answer": "A1", "difficulty": "easy"},
        ],
    )
    cards = client.post("/flashcards/generate", json={"document_id": doc_id, "count": 1}, headers=headers).json()
    card_id = cards[0]["id"]

    resp = client.post("/flashcards/review", json={"flashcard_id": card_id, "got_it_right": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["new_retention"] > 0.5


def test_review_decreases_retention_on_wrong_answer(client, registered_user, monkeypatch):
    _, _, headers = registered_user
    doc_id = _upload_document(client, headers, monkeypatch)
    monkeypatch.setattr(
        "app.routers.flashcards.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3000: [
            {"question": "Q1", "answer": "A1", "difficulty": "easy"},
        ],
    )
    cards = client.post("/flashcards/generate", json={"document_id": doc_id, "count": 1}, headers=headers).json()
    card_id = cards[0]["id"]

    resp = client.post("/flashcards/review", json={"flashcard_id": card_id, "got_it_right": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["new_retention"] < 0.5


def test_cannot_review_another_users_flashcard(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.upload.pdf_processor.extract_pages",
        lambda path: [(1, "content")],
    )
    monkeypatch.setattr(
        "app.routers.flashcards.llm_service.generate_json",
        lambda system, user_prompt, max_tokens=3000: [{"question": "Q", "answer": "A", "difficulty": "easy"}],
    )

    client.post("/auth/register", json={"email": "owner@example.com", "password": "pass12345", "name": "Owner"})
    login_owner = client.post(
        "/auth/login",
        data={"username": "owner@example.com", "password": "pass12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers_owner = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}
    doc_id = _upload_document(client, headers_owner, monkeypatch)
    card_id = client.post(
        "/flashcards/generate", json={"document_id": doc_id, "count": 1}, headers=headers_owner
    ).json()[0]["id"]

    client.post("/auth/register", json={"email": "intruder@example.com", "password": "pass12345", "name": "Intruder"})
    login_intruder = client.post(
        "/auth/login",
        data={"username": "intruder@example.com", "password": "pass12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers_intruder = {"Authorization": f"Bearer {login_intruder.json()['access_token']}"}

    resp = client.post(
        "/flashcards/review", json={"flashcard_id": card_id, "got_it_right": True}, headers=headers_intruder
    )
    assert resp.status_code == 404
