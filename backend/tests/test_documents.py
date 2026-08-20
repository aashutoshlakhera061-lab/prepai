"""Tests for PDF upload. Mocks the actual PDF parsing so tests don't depend
on a real file on disk or PDF-library internals — they test OUR logic
(the endpoint, the DB writes, the ownership checks), not pypdf itself."""
import io


def test_upload_requires_authentication(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", fake_pdf, "application/pdf")},
        data={"subject": "Java"},
    )
    assert resp.status_code == 401


def test_upload_rejects_non_pdf(client, registered_user):
    _, _, headers = registered_user
    fake_txt = io.BytesIO(b"just plain text, not a pdf")
    resp = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", fake_txt, "text/plain")},
        data={"subject": "Java"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_upload_extracts_and_stores_chunks(client, registered_user, monkeypatch):
    _, _, headers = registered_user

    # Mock PDF extraction so this test doesn't depend on a real PDF file.
    monkeypatch.setattr(
        "app.routers.upload.pdf_processor.extract_pages",
        lambda path: [(1, "Polymorphism lets an object take multiple forms.")],
    )

    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content for testing")
    resp = client.post(
        "/documents/upload",
        files={"file": ("java_notes.pdf", fake_pdf, "application/pdf")},
        data={"subject": "Java"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "java_notes.pdf"
    assert body["subject"] == "Java"
    assert "id" in body


def test_users_only_see_their_own_documents(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.upload.pdf_processor.extract_pages",
        lambda path: [(1, "Some study content here.")],
    )

    # User A uploads a document
    client.post("/auth/register", json={"email": "a@example.com", "password": "pass12345", "name": "A"})
    login_a = client.post(
        "/auth/login",
        data={"username": "a@example.com", "password": "pass12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    client.post(
        "/documents/upload",
        files={"file": ("a_notes.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        data={"subject": "General"},
        headers=headers_a,
    )

    # User B should see an empty document list, not User A's document
    client.post("/auth/register", json={"email": "b@example.com", "password": "pass12345", "name": "B"})
    login_b = client.post(
        "/auth/login",
        data={"username": "b@example.com", "password": "pass12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
    resp = client.get("/documents/", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []
