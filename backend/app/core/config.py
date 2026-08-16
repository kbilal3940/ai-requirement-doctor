"""
Centralized app configuration, loaded from environment variables (.env).
Keep every tunable (model name, CORS origin, limits) here so the rest of
the codebase never reads os.environ directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- AI provider selection ---
    # "gemini" or "groq". Everything downstream (ai_client.py) branches on
    # this one switch, so swapping providers never touches code — just env.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model is configurable so it can be swapped without touching code.
    # NOTE: Gemini's naming scheme uses "flash" tiers (e.g. gemini-1.5-flash,
    # gemini-flash-latest) rather than version numbers like "3.5" (that
    # naming belongs to a different provider's model family). Point this
    # at whatever current Gemini Flash model string your API key has
    # access to.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    GEMINI_API_BASE: str = os.getenv(
        "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
    )
    GEMINI_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Groq deprecated its Llama 3.x chat models in mid-2026; the current
    # recommended general-purpose model is the gpt-oss line. Configurable
    # for the same reason as GEMINI_MODEL above.
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_API_BASE: str = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
    GROQ_TIMEOUT_SECONDS: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))

    # --- App / CORS ---
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    # --- Input limits ---
    MAX_REQUIREMENT_CHARS: int = int(os.getenv("MAX_REQUIREMENT_CHARS", "5000"))
    MIN_REQUIREMENT_CHARS: int = int(os.getenv("MIN_REQUIREMENT_CHARS", "10"))


settings = Settings()