import datetime
from app.database import Base, utcnow
from sqlalchemy import (
    Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, default="")
    created_at = Column(DateTime, default=utcnow)

    documents = relationship("Document", back_populates="owner")
    attempts = relationship("MockTestAttempt", back_populates="user")
    mistakes = relationship("Mistake", back_populates="user")


class Document(Base):
    """An uploaded PDF/notes file that becomes a private knowledge base."""
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    subject = Column(String, default="General")
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """A chunk of text from a document, used for RAG retrieval (TF-IDF based)."""
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    text = Column(Text, nullable=False)
    page = Column(Integer, default=0)
    order_index = Column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")


class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(String, default="medium")  # easy/medium/hard
    retention = Column(Float, default=0.5)  # 0..1, updated by spaced-repetition logic
    times_reviewed = Column(Integer, default=0)
    last_reviewed = Column(DateTime, nullable=True)
    next_due = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="flashcards")


class MockTest(Base):
    __tablename__ = "mock_tests"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    subject = Column(String, default="General")
    difficulty = Column(String, default="medium")
    questions = Column(JSON, nullable=False)  # list of {question, options, correct_index, source}
    created_at = Column(DateTime, default=utcnow)


class MockTestAttempt(Base):
    __tablename__ = "mock_test_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mock_test_id = Column(Integer, ForeignKey("mock_tests.id"))
    answers = Column(JSON, nullable=False)  # list of selected indices
    score_pct = Column(Float, default=0.0)
    topic_breakdown = Column(JSON, default=dict)  # {topic: pct}
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="attempts")


class Mistake(Base):
    """Mistake Book: every wrong answer, categorized."""
    __tablename__ = "mistakes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String, default="General")
    question = Column(Text, nullable=False)
    user_answer = Column(Text, default="")
    correct_answer = Column(Text, default="")
    category = Column(String, default="conceptual")  # conceptual/memory/logic/careless/misunderstood/time_pressure
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="mistakes")
