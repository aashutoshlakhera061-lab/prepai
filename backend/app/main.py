import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth, upload, summary, flashcards, mocktest, dashboard, chat, mistakes

logger = logging.getLogger("prepai")


def _validate_llm_config():
    """Fail fast and loudly at startup if the LLM provider is misconfigured,
    rather than letting the first user request crash deep in llm_service.py
    with a confusing stack trace."""
    provider = settings.llm_provider.lower()
    key_map = {
        "anthropic": settings.anthropic_api_key,
        "groq": settings.groq_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    if provider not in key_map:
        raise RuntimeError(
            f"Invalid LLM_PROVIDER='{settings.llm_provider}' in .env. "
            "Must be one of: anthropic, groq, openrouter."
        )
    if not key_map[provider]:
        env_var = f"{provider.upper()}_API_KEY"
        raise RuntimeError(
            f"LLM_PROVIDER is set to '{provider}' but {env_var} is empty in .env. "
            f"Set {env_var} to a real API key before starting the server."
        )
    logger.info(f"LLM provider configured: {provider} (model={settings.llm_model})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _validate_llm_config()
    yield


Base.metadata.create_all(bind=engine)

app = FastAPI(title="PrepAI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # add your deployed frontend URL here too
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(summary.router)
app.include_router(flashcards.router)
app.include_router(mocktest.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(mistakes.router)


@app.get("/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider}
