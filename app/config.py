from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TelegramConfig:
    token: str = ""
    chat_id: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)


@dataclass
class Profile:
    name: str
    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    required_keywords: list[str] = field(default_factory=list)
    excluded_keywords: list[str] = field(default_factory=list)
    exclude_companies: list[str] = field(default_factory=list)
    employment_types: list[str] = field(default_factory=list)
    experience_levels: list[str] = field(default_factory=list)
    max_age_minutes: int | None = None
    sources: list[str] = field(default_factory=lambda: ["linkedin"])
    remote: bool | None = None
    enabled: bool = True
    interval: int | None = None
    notifications: bool = True


@dataclass
class Config:
    interval: int = 300
    database: str = "jobs.db"
    profiles: list[Profile] = field(default_factory=list)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    request_timeout: int = 30
    retries: int = 3


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def load_config(path: str | Path = "config.yaml") -> Config:
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    general = raw.get("general", {}) or {}
    database = raw.get("database", "jobs.db")
    if isinstance(database, dict):
        database = database.get("sqlite_db", database.get("path", "jobs.db"))
    telegram = raw.get("telegram", {}) or {}
    profiles = []
    for item in raw.get("profiles", []) or []:
        if isinstance(item, str):
            item = {"name": item}
        profiles.append(Profile(
            name=str(item.get("name", "unnamed")),
            keywords=_list(item.get("keywords")),
            locations=_list(item.get("locations")),
            required_keywords=_list(item.get("required_keywords")),
            excluded_keywords=_list(item.get("excluded_keywords")),
            exclude_companies=_list(item.get("exclude_companies")),
            employment_types=_list(item.get("employment_type", item.get("employment_types"))),
            experience_levels=_list(item.get("experience", item.get("experience_levels"))),
            max_age_minutes=(
                int(item["max_age_minutes"])
                if item.get("max_age_minutes") is not None
                else None
            ),
            sources=_list(item.get("sources", ["linkedin"])),
            remote=item.get("remote"),
            enabled=bool(item.get("enabled", True)),
            interval=item.get("interval"),
            notifications=bool(item.get("notifications", True)),
        ))
    if not profiles:
        raise ValueError("config must contain at least one profile")
    config = Config(
        interval=int(os.getenv("JOB_MONITOR_INTERVAL") or general.get("interval", raw.get("interval", 300))),
        database=os.getenv("JOB_MONITOR_DATABASE") or str(database),
        profiles=profiles,
        telegram=TelegramConfig(
            os.getenv("TELEGRAM_BOT_TOKEN") or str(telegram.get("token", "")),
            os.getenv("TELEGRAM_CHAT_ID") or str(telegram.get("chat_id", "")),
        ),
        request_timeout=int(general.get("request_timeout", 30)),
        retries=int(general.get("retries", 3)),
    )
    if config.interval <= 0 or config.retries < 1:
        raise ValueError("interval must be positive and retries must be at least 1")
    return config
