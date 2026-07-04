from __future__ import annotations

from collections import defaultdict

from arbitrage_bot.models import ArbitrageOpportunity, BestOutcome, _stake_key


def calculate_stakes(prices: dict[str, float], total_stake: float) -> dict[str, float]:
    """Split total_stake across outcomes so the payout is identical no matter which wins.

    stake_i = total_stake * (1/price_i) / sum(1/price_j for all j)
    """
    inverse_prices = {key: 1.0 / price for key, price in prices.items()}
    inverse_sum = sum(inverse_prices.values())
    return {key: total_stake * inv / inverse_sum for key, inv in inverse_prices.items()}


def _best_outcomes_by_point(event: dict, market_key: str) -> dict[float | None, dict[str, BestOutcome]]:
    """Group the best (highest) price per outcome name, keyed by point (line) then name.

    Grouping by point first keeps different lines (e.g. Over/Under 2.5 vs 3.5)
    from being treated as one arbitrage market.
    """
    groups: dict[float | None, dict[str, BestOutcome]] = defaultdict(dict)
    for bookmaker in event.get("bookmakers", []):
        bookmaker_name = bookmaker.get("title") or bookmaker.get("key", "unknown")
        for market in bookmaker.get("markets", []):
            if market.get("key") != market_key:
                continue
            for outcome in market.get("outcomes", []):
                point = outcome.get("point")
                name = outcome["name"]
                price = float(outcome["price"])
                current = groups[point].get(name)
                if current is None or price > current.price:
                    groups[point][name] = BestOutcome(
                        name=name, point=point, price=price, bookmaker=bookmaker_name
                    )
    return groups


def find_arbitrage(
    events: list[dict],
    market_keys: list[str],
    min_profit_percent: float,
    total_stake: float,
) -> list[ArbitrageOpportunity]:
    opportunities: list[ArbitrageOpportunity] = []

    for event in events:
        for market_key in market_keys:
            groups = _best_outcomes_by_point(event, market_key)
            for point, outcomes_by_name in groups.items():
                if len(outcomes_by_name) < 2:
                    continue

                prices = {name: bo.price for name, bo in outcomes_by_name.items()}
                inverse_sum = sum(1.0 / price for price in prices.values())
                if inverse_sum >= 1.0:
                    continue

                profit_percent = (1.0 / inverse_sum - 1.0) * 100
                if profit_percent < min_profit_percent:
                    continue

                outcomes = list(outcomes_by_name.values())
                stakes_by_name = calculate_stakes(prices, total_stake)
                stakes = {_stake_key(o): stakes_by_name[o.name] for o in outcomes}

                opportunities.append(
                    ArbitrageOpportunity(
                        sport_key=event.get("sport_key", ""),
                        event_id=event.get("id", ""),
                        home_team=event.get("home_team", ""),
                        away_team=event.get("away_team", ""),
                        commence_time=event.get("commence_time", ""),
                        market_key=market_key,
                        point=point,
                        outcomes=outcomes,
                        profit_percent=profit_percent,
                        stakes=stakes,
                    )
                )

    return opportunities
