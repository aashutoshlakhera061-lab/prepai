"""Shared pytest fixtures. Tests run against an isolated in-memory SQLite
database — never your real prepai.db — so they're safe to run anytime and
leave no side effects.

IMPORTANT: DATABASE_URL must be overridden BEFORE app.main is imported,
since app.config.settings is instantiated at import time. That's why this
line comes before any `from app...` import below.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "./test_uploads"
# The app now validates at startup that an API key exists for the configured
# LLM provider (see main.py's lifespan). Tests never call a real LLM — every
# test mocks app.routers.*.llm_service.generate_text/generate_json — so this
# dummy key only exists to satisfy that startup check.
os.environ.setdefault("LLM_PROVIDER", "anthropic")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture()
def db_session():
    # StaticPool is required for SQLite ":memory:" in tests: without it,
    # SQLAlchemy hands out a NEW connection (= a brand new, empty database)
    # per checkout, so the tables created here would be invisible to any
    # query the app runs later. StaticPool forces every checkout to reuse
    # the same single connection, so the schema persists for the whole test.
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """Registers a user and returns (email, password, auth_headers)."""
    email = "testuser@example.com"
    password = "testpassword123"
    client.post("/auth/register", json={"email": email, "password": password, "name": "Test User"})
    login_resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_resp.json()["access_token"]
    return email, password, {"Authorization": f"Bearer {token}"}