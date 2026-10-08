"""Application configuration. All settings come from environment variables (see /.env.example)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]  # apps/api
REPO_ROOT = API_ROOT.parents[1]


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
    max_upload_mb: int = Field(default=15, ge=1, le=100)

    inference_provider: Literal["rule_based", "openai_compat"] = "rule_based"
    inference_base_url: str = "http://localhost:8001/v1"
    inference_model: str = "Qwen/Qwen2.5-7B-Instruct"
    inference_api_key: str = ""
    inference_timeout_s: float = 60.0
    inference_hardware_label: str = "local-cpu"

    safety_min_page_quality: float = Field(default=0.85, ge=0.0, le=1.0)
    safety_min_fact_confidence: float = Field(default=0.80, ge=0.0, le=1.0)

    @property
    def resolved_database_url(self) -> str:
        """Postgres when configured; otherwise a local SQLite file formatted safely for any OS."""
        if self.database_url:
            return self.database_url
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
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
