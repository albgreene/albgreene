from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    api_key: str
    sports: list[str] = field(default_factory=lambda: ["upcoming"])
    regions: str = "us,uk,eu,au"
    markets: list[str] = field(default_factory=lambda: ["h2h"])
    min_profit_percent: float = 1.0
    poll_interval_seconds: int = 300
    total_stake: float = 100.0
    log_file: str = "arbitrage_log.jsonl"


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config(env: dict | None = None) -> Config:
    env = env if env is not None else os.environ

    api_key = env.get("ODDS_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ODDS_API_KEY is not set. Get a free key from https://the-odds-api.com/ "
            "and put it in your .env file or environment."
        )

    return Config(
        api_key=api_key,
        sports=_split_csv(env.get("SPORTS", "upcoming")),
        regions=env.get("REGIONS", "us,uk,eu,au"),
        markets=_split_csv(env.get("MARKETS", "h2h")),
        min_profit_percent=float(env.get("MIN_PROFIT_PERCENT", "1.0")),
        poll_interval_seconds=int(env.get("POLL_INTERVAL_SECONDS", "300")),
        total_stake=float(env.get("TOTAL_STAKE", "100")),
        log_file=env.get("LOG_FILE", "arbitrage_log.jsonl"),
    )
