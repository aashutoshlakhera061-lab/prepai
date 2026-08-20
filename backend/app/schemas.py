from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import datetime


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class UserOut(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Documents ----
class DocumentOut(BaseModel):
    id: int
    filename: str
    subject: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- Summary ----
class SummaryRequest(BaseModel):
    document_id: int
    mode: str = "quick"  # quick | detailed | interview | cheatsheet


class SummaryResponse(BaseModel):
    mode: str
    content: str


# ---- Flashcards ----
class FlashcardOut(BaseModel):
    id: int
    question: str
    answer: str
    difficulty: str
    retention: float

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    flashcard_id: int
    got_it_right: bool


class FlashcardGenerateRequest(BaseModel):
    document_id: int
    count: int = 15


# ---- Mock tests ----
class MockTestGenerateRequest(BaseModel):
    document_id: int
    difficulty: str = "medium"
    num_questions: int = 10


class MockTestQuestion(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    topic: str
    source: str = ""


class MockTestOut(BaseModel):
    id: int
    subject: str
    difficulty: str
    questions: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class MockTestSubmit(BaseModel):
    mock_test_id: int
    answers: List[int]  # selected option index per question, -1 if skipped


class MockTestResult(BaseModel):
    score_pct: float
    topic_breakdown: Dict[str, float]
    mistakes_logged: int


# ---- Chat ----
class ChatRequest(BaseModel):
    document_id: int
    message: str
    history: List[Dict[str, str]] = []  # [{role, content}]


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []


# ---- Dashboard ----
class DashboardOut(BaseModel):
    interview_readiness: float
    topic_scores: Dict[str, float]
    mock_tests_taken: int
    flashcards_reviewed: int
    top_priority_topic: Optional[str]
    accuracy_trend: List[float]


# ---- Mistakes ----
class MistakeOut(BaseModel):
    id: int
    topic: str
    question: str
    category: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
