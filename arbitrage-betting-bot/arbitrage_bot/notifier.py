from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from arbitrage_bot.models import ArbitrageOpportunity


class Notifier(ABC):
    @abstractmethod
    def notify(self, opportunities: list[ArbitrageOpportunity]) -> None: ...


class ConsoleNotifier(Notifier):
    def notify(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not opportunities:
            print("No arbitrage opportunities found.")
            return

        for opp in opportunities:
            line_label = f" (line {opp.point})" if opp.point is not None else ""
            print(
                f"[ARBITRAGE] {opp.away_team} @ {opp.home_team} "
                f"({opp.market_key}{line_label}) - {opp.profit_percent:.2f}% guaranteed profit"
            )
            for outcome in opp.outcomes:
                stake = opp.stakes[f"{outcome.name}|{outcome.bookmaker}"]
                print(f"    bet {stake:.2f} on {outcome.name} @ {outcome.price} ({outcome.bookmaker})")


class FileNotifier(Notifier):
    def __init__(self, path: str):
        self.path = path

    def notify(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not opportunities:
            return
        with open(self.path, "a", encoding="utf-8") as f:
            for opp in opportunities:
                record = opp.to_dict()
                record["found_at"] = datetime.now(timezone.utc).isoformat()
                f.write(json.dumps(record) + "\n")
