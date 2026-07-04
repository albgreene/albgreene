from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BestOutcome:
    """The best available price for one outcome, and which bookmaker offers it."""

    name: str
    point: float | None
    price: float
    bookmaker: str


@dataclass
class ArbitrageOpportunity:
    sport_key: str
    event_id: str
    home_team: str
    away_team: str
    commence_time: str
    market_key: str
    point: float | None
    outcomes: list[BestOutcome]
    profit_percent: float
    stakes: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "sport_key": self.sport_key,
            "event_id": self.event_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "commence_time": self.commence_time,
            "market_key": self.market_key,
            "point": self.point,
            "profit_percent": round(self.profit_percent, 3),
            "outcomes": [
                {
                    "name": o.name,
                    "point": o.point,
                    "price": o.price,
                    "bookmaker": o.bookmaker,
                    "stake": round(self.stakes[_stake_key(o)], 2),
                }
                for o in self.outcomes
            ],
        }


def _stake_key(outcome: BestOutcome) -> str:
    return f"{outcome.name}|{outcome.bookmaker}"
