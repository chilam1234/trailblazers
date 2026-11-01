from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from meridian.schemas import Company, Document
from meridian.settings import settings


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_companies() -> dict[str, Company]:
    out: dict[str, Company] = {}
    for path in sorted((settings.fixtures_dir / "companies").glob("*.json")):
        raw = _load_json(path)
        company = Company.model_validate(raw)
        out[company.ticker] = company
    return out


@lru_cache(maxsize=1)
def load_documents() -> list[Document]:
    docs: list[Document] = []
    for path in sorted((settings.fixtures_dir / "filings").glob("*.json")):
        raw = _load_json(path)
        docs.append(
            Document(
                id=raw["id"],
                kind="filing",
                ticker=raw["ticker"],
                title=raw["title"],
                text=raw["text"],
                filed=raw.get("filed", ""),
                form=raw.get("form", ""),
            )
        )
    for path in sorted((settings.fixtures_dir / "news").glob("*.json")):
        raw = _load_json(path)
        docs.append(
            Document(
                id=raw["id"],
                kind="news",
                ticker=raw["ticker"],
                title=raw["title"],
                text=raw["text"],
                filed=raw.get("published", ""),
                form="news",
            )
        )
    return docs


def company_alias_index() -> list[tuple[str, str]]:
    """(alias_lower, ticker) pairs, longest alias first."""
    pairs: list[tuple[str, str]] = []
    for company in load_companies().values():
        names = [company.ticker, company.name, *company.aliases]
        for name in names:
            pairs.append((name.lower(), company.ticker))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs
