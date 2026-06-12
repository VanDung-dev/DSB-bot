import logging
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    return int(val) if val is not None else default


def _env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    return float(val) if val is not None else default


def _env_log_level(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    return getattr(logging, val.upper(), default)


def _env_color(key: str, default: int) -> int:
    val = os.getenv(key)
    return int(val, 16) if val is not None else default


class Config:
    # ── Bot ──
    BOT_NAME: str = _env_str("BOT_NAME", "DSB Bot")
    COMMAND_PREFIX: str = _env_str("COMMAND_PREFIX", "!")

    # ── Logging ──
    LOG_FORMAT: str = "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    LOG_DATE: str = "%Y-%m-%d %H:%M:%S"
    LOG_LEVEL: int = _env_log_level("LOG_LEVEL", logging.INFO)
    LOG_COLORS: dict[str, str] = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }

    # ── Embed ──
    _default_footer: str = _env_str("BOT_NAME", "DSB Bot")
    EMBED_FOOTER: str = _env_str("EMBED_FOOTER", _default_footer)
    EMBED_COLOR: int = _env_color("EMBED_COLOR", 0x00FF88)
    CHUNK_SIZE: int = _env_int("CHUNK_SIZE", 1900)

    # ── Memory / Context ──
    MEMORY_LIMIT: int = _env_int("MEMORY_LIMIT", 40)

    # ── AI / OpenRouter ──
    AI_MODEL: str = _env_str("AI_MODEL", "openai/gpt-oss-20b:free")
    OPENROUTER_API_URL: str = _env_str("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    AI_TEMPERATURE: float = _env_float("AI_TEMPERATURE", 0.7)
    AI_TOP_P: float = _env_float("AI_TOP_P", 0.8)
    AI_MAX_TOKENS: int = _env_int("AI_MAX_TOKENS", 128000)
    AI_MAX_RETRIES: int = _env_int("AI_MAX_RETRIES", 3)
    AI_RETRY_DELAY: float = _env_float("AI_RETRY_DELAY", 2.0)
    SYSTEM_PROMPT_FILE: str = _env_str("SYSTEM_PROMPT_FILE", "system_prompt.md")
    FALLBACK_SYSTEM_PROMPT: str = _env_str("FALLBACK_SYSTEM_PROMPT", "You are a helpful assistant.")

    # ── R34 ──
    R34_MAX_RESULTS: int = _env_int("R34_MAX_RESULTS", 1)

    @property
    def r34_api_key(self) -> str:
        return os.getenv("R34_API_KEY", "")

    @property
    def r34_user_id(self) -> str:
        return os.getenv("R34_USER_ID", "")

    # ── Owner ──
    OWNER_ID: int | None = _env_int("OWNER_ID", 0) or None

    # ── Required env-based ──

    @property
    def discord_token(self) -> str:
        return self._require("KEY_DISCORD")

    @property
    def openrouter_api_key(self) -> str:
        return os.getenv("OPENROUTER_API_KEY", "")



    @staticmethod
    def _require(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"❌ {name} is not set in .env")
        return value


@lru_cache
def get_config() -> Config:
    return Config()
