"""LLM wrapper supporting three interchangeable providers:

  - anthropic   -> Claude, via Anthropic's native Messages API
  - groq        -> open-weight models (Llama, GPT-OSS, etc.) via Groq's
                    OpenAI-compatible endpoint, extremely fast inference
  - openrouter  -> 300+ models (including Claude, GPT, Gemini, Llama, and
                    free-tier models) via OpenRouter's OpenAI-compatible
                    endpoint, billed from one balance

Switch providers by setting LLM_PROVIDER + LLM_MODEL (+ the matching API key)
in .env — no other code in the app needs to change, since every router calls
only generate_text() / generate_json() below.
"""
import json
import re
from app.config import settings

_client = None


def _get_client():
    """Lazily builds and caches the right client for the configured provider."""
    global _client
    if _client is not None:
        return _client

    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from anthropic import Anthropic
        _client = Anthropic(api_key=settings.anthropic_api_key)

    elif provider == "groq":
        from openai import OpenAI
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    elif provider == "openrouter":
        from openai import OpenAI
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use 'anthropic', 'groq', or 'openrouter'."
        )

    return _client


def _extract_json(text: str):
    """Models sometimes wrap JSON in prose or code fences; this pulls out
    the first valid JSON array/object it finds."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate_text(system: str, user_prompt: str, max_tokens: int = 1500) -> str:
    from fastapi import HTTPException

    provider = settings.llm_provider.lower()
    client = _get_client()

    try:
        if provider == "anthropic":
            resp = client.messages.create(
                model=settings.llm_model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return "".join(block.text for block in resp.content if block.type == "text")

        # groq and openrouter both speak the OpenAI chat.completions shape
        extra_headers = {}
        if provider == "openrouter":
            if settings.openrouter_site_url:
                extra_headers["HTTP-Referer"] = settings.openrouter_site_url
            if settings.openrouter_app_name:
                extra_headers["X-Title"] = settings.openrouter_app_name

        resp = client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            extra_headers=extra_headers or None,
        )
        return resp.choices[0].message.content or ""

    except Exception as e:
        # Translate provider rate-limit errors into a clean message instead
        # of a raw stack trace / API error dump reaching the user.
        msg = str(e).lower()
        if "rate_limit" in msg or "429" in msg or "413" in msg or "tokens per minute" in msg:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"The {provider} API rate limit was hit for this request "
                    "(this document/request may be too large for the free tier). "
                    "Try again with fewer questions/flashcards, a shorter document, "
                    "or wait about a minute and retry."
                ),
            )
        raise


def generate_json(system: str, user_prompt: str, max_tokens: int = 2000):
    """Asks the model to respond with ONLY JSON, then parses it."""
    from fastapi import HTTPException
    import json as _json

    raw = generate_text(
        system=system + "\n\nRespond with ONLY valid JSON. No prose, no markdown fences.",
        user_prompt=user_prompt,
        max_tokens=max_tokens,
    )
    try:
        return _extract_json(raw)
    except _json.JSONDecodeError:
        # Most common cause: the model's response got cut off mid-JSON
        # because max_tokens ran out before it finished (e.g. too many
        # questions/flashcards requested for the token budget). Rather
        # than crash with a raw parser stack trace, tell the user what to try.
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI's response wasn't valid JSON — this usually happens when "
                "the response got cut off because too much content was requested "
                "at once. Try again with fewer questions/flashcards, or a shorter "
                "document."
            ),
        )
