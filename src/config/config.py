from dataclasses import dataclass, field
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def require_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Environment variable '{key}' is required but not set.")
    return value


def require_int_env(key: str, default: Optional[int] = None) -> int:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        if default is not None:
            return default
        raise RuntimeError(f"Environment variable '{key}' is required but not set.")
    try:
        ivalue = int(value)
        if ivalue < 0:
            raise ValueError
        return ivalue
    except ValueError:
        raise RuntimeError(f"Environment variable '{key}' must be a non-negative integer.")


@dataclass
class Config:
    MONGODB_URI: str = field(default_factory=lambda: require_env("MONGODB_URI"))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    CACHE_TTL: int = field(default_factory=lambda: require_int_env("CACHE_TTL", default=3600))
    MAX_MESSAGES_PER_REQUEST: int = field(
        default_factory=lambda: require_int_env("MAX_MESSAGES_PER_REQUEST", default=100)
    )
    OPENAI_API_KEY: str = field(default_factory=lambda: require_env("OPENAI_API_KEY"))
    DB_NAME: str = field(default_factory=lambda: require_env("DB_NAME"))
    JWT_SECRET_KEY: str = field(default_factory=lambda: require_env("JWT_SECRET_KEY"))
    QDRANT_API_URL: str = field(default_factory=lambda: require_env("QDRANT_API_URL"))
    QDRANT_API_KEY: str = field(default_factory=lambda: require_env("QDRANT_API_KEY"))
    EMAIL_APP_PASSWORD: str = field(default_factory=lambda: require_env("EMAIL_PASSWORD"))
    AI_ML_API_KEY: str = field(default_factory=lambda: require_env("AI_ML_API"))
    SERVICE: str = field(default_factory=lambda: require_env("SERVICE"))


config = Config()
