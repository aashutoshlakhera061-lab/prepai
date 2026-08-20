from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Which provider to call: "anthropic" | "groq" | "openrouter"
    llm_provider: str = "anthropic"

    # Model id to use — the meaning depends on llm_provider (see .env.example
    # for current recommended values per provider).
    llm_model: str = "claude-sonnet-4-6"

    # Provider credentials — only the one matching llm_provider needs to be set.
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    # Optional, only used for OpenRouter's leaderboard attribution headers.
    openrouter_site_url: str = ""
    openrouter_app_name: str = "PrepAI"

    database_url: str = "sqlite:///./prepai.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"


settings = Settings()
