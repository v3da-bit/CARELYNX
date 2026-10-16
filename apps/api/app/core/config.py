"""Application configuration. All settings come from environment variables (see /.env.example)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]  # apps/api
REPO_ROOT = API_ROOT.parent.parent  # .parents[1] raises IndexError when the API lives at /app


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(API_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = ""
    cors_origins: str = "http://localhost:3000"

    storage_backend: Literal["local"] = "local"
    storage_local_dir: str = "./var/storage"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    auth_secret_key: str = "carelynx-sec-key-778899aabbccddeeff00112233445566"
    firebase_project_id: str = "buttler-8e847"
    debug: bool = False

    # Inference provider: `gemini`, `openai_compat`, or `rule_based`
    # `openai_compat` is the settings key; `openai_compatible` is accepted as a docs alias.
    inference_provider: Literal["rule_based", "gemini", "openai_compat", "openai_compatible"] = "rule_based"
    inference_base_url: str = "http://localhost:8080/v1"
    inference_model: str = "Qwen/Qwen2.5-7B-Instruct"
    inference_api_key: str = ""
    gemini_api_key: str = ""
    inference_timeout_s: float = 60.0
    inference_hardware_label: str = "local-cpu"

    google_translate_api_key: str = ""

    safety_min_page_quality: float = Field(default=0.85, ge=0.0, le=1.0)
    safety_min_fact_confidence: float = Field(default=0.80, ge=0.0, le=1.0)

    @property
    def resolved_database_url(self) -> str:
        """Postgres when configured; otherwise a local SQLite file formatted safely for any OS."""
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg://", 1)
            if url.startswith("postgresql://") and not url.startswith("postgresql+"):
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
        var_dir = API_ROOT / "var"
        var_dir.mkdir(parents=True, exist_ok=True)
        db_path = (var_dir / "carelynx.db").resolve().as_posix()
        return f"sqlite:///{db_path}"

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_local_dir)
        if not p.is_absolute():
            p = (API_ROOT / p).resolve()
        else:
            p = p.resolve()
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        """Credentials cannot be used with wildcard origins (browser security spec)."""
        return "*" not in self.cors_origin_list


@lru_cache
def get_settings() -> Settings:
    return Settings()
