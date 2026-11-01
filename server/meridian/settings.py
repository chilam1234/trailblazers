from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "fixtures").is_dir() and (parent / "server").is_dir():
            return parent
    return here.parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    rate_limit_per_min: int = 60
    rate_burst: int = 20
    cache_jaccard_threshold: float = 0.82
    eval_gate: float = 0.92

    repo_root: Path = _repo_root()

    @property
    def fixtures_dir(self) -> Path:
        return self.repo_root / "fixtures"

    @property
    def last_run_path(self) -> Path:
        return self.repo_root / "evals" / "last-run.json"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
