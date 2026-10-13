"""Environment-backed configuration for the VoC pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    api_key: str | None = os.getenv("GEMINI_API_KEY")
    request_timeout_seconds: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))
    max_retries: int = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    retry_base_seconds: float = float(os.getenv("GEMINI_RETRY_BASE_SECONDS", "1.5"))
    min_request_interval_seconds: float = float(os.getenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "8"))
    input_usd_per_million_tokens: float | None = float(os.environ["GEMINI_INPUT_USD_PER_MILLION_TOKENS"]) if os.getenv("GEMINI_INPUT_USD_PER_MILLION_TOKENS") else None
    output_usd_per_million_tokens: float | None = float(os.environ["GEMINI_OUTPUT_USD_PER_MILLION_TOKENS"]) if os.getenv("GEMINI_OUTPUT_USD_PER_MILLION_TOKENS") else None
    data_dir: Path = ROOT / "data"


settings = Settings()
