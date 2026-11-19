"""Satu-satunya tempat membaca .env dan membuat model LLM."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ("LLM_MODEL", "LLM_API_BASE", "LLM_API_KEY")


@dataclass(frozen=True)
class Settings:
    llm_model: str
    llm_api_base: str
    llm_api_key: str
    llm_api_version: str = ""
    ragflow_base_url: str = "http://localhost:9380"
    ragflow_api_key: str = ""
    ragflow_embedding_model: str = ""
    lightrag_workspaces: dict[str, str] = field(default_factory=dict)
    lightrag_api_key: str = ""
    embedding_deployment: str = "text-embedding-3-small"


def _parse_workspaces(raw: str) -> dict[str, str]:
    """'Nama A=http://..,Nama B=http://..' -> {'Nama A': 'http://..', ...}"""
    pairs = (item.split("=", 1) for item in raw.split(",") if "=" in item)
    return {name.strip(): url.strip() for name, url in pairs}


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    if env is None:
        load_dotenv(PROJECT_ROOT / ".env")
        env = os.environ
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        raise ValueError(f"Variabel .env wajib belum diisi: {', '.join(missing)} (lihat .env.example)")
    return Settings(
        llm_model=env["LLM_MODEL"],
        llm_api_base=env["LLM_API_BASE"],
        llm_api_key=env["LLM_API_KEY"],
        llm_api_version=env.get("LLM_API_VERSION", ""),
        ragflow_base_url=env.get("RAGFLOW_BASE_URL") or "http://localhost:9380",
        ragflow_api_key=env.get("RAGFLOW_API_KEY", ""),
        ragflow_embedding_model=env.get("RAGFLOW_EMBEDDING_MODEL", ""),
        lightrag_workspaces=_parse_workspaces(env.get("LIGHTRAG_WORKSPACES", "")),
        lightrag_api_key=env.get("LIGHTRAG_API_KEY", ""),
        embedding_deployment=env.get("EMBEDDING_DEPLOYMENT") or "text-embedding-3-small",
    )


def make_model(settings: Settings):
    """Model LLM untuk semua agent (LiteLLM -> Azure OpenAI)."""
    from google.adk.models.lite_llm import LiteLlm

    kwargs = {"model": settings.llm_model, "api_base": settings.llm_api_base, "api_key": settings.llm_api_key}
    if settings.llm_api_version:
        kwargs["api_version"] = settings.llm_api_version
    return LiteLlm(**kwargs)
