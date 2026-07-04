import math

import pytest

from arbitrage_bot.arbitrage import calculate_stakes, find_arbitrage


def make_event(sport_key, event_id, home, away, commence_time, bookmaker_odds, market_key="h2h"):
    """bookmaker_odds: dict of bookmaker_name -> {outcome_name: price}"""
    bookmakers = []
    for name, outcomes in bookmaker_odds.items():
        bookmakers.append(
            {
                "key": name.lower().replace(" ", "_"),
                "title": name,
                "markets": [
                    {
                        "key": market_key,
                        "outcomes": [{"name": o, "price": p} for o, p in outcomes.items()],
                    }
                ],
            }
        )
    return {
        "id": event_id,
        "sport_key": sport_key,
        "home_team": home,
        "away_team": away,
        "commence_time": commence_time,
        "bookmakers": bookmakers,
    }


def test_calculate_stakes_payout_is_identical_per_outcome():
    prices = {"Team A": 2.10, "Team B": 2.05}
    stakes = calculate_stakes(prices, total_stake=100.0)

    payouts = {name: stakes[name] * price for name, price in prices.items()}
    payout_values = list(payouts.values())

    assert math.isclose(payout_values[0], payout_values[1], rel_tol=1e-9)
    assert math.isclose(sum(stakes.values()), 100.0, rel_tol=1e-9)


def test_finds_two_way_arbitrage_opportunity():
    event = make_event(
        "soccer_epl",
        "evt1",
        "Team A",
        "Team B",
        "2026-08-01T18:00:00Z",
        {
            "Bookmaker One": {"Team A": 2.10, "Team B": 1.80},
            "Bookmaker Two": {"Team A": 1.85, "Team B": 2.05},
        },
    )

    opportunities = find_arbitrage([event], ["h2h"], min_profit_percent=0.5, total_stake=100.0)

    assert len(opportunities) == 1
    opp = opportunities[0]
    assert opp.profit_percent > 0.5

    prices_used = {o.name: o.price for o in opp.outcomes}
    assert prices_used == {"Team A": 2.10, "Team B": 2.05}

    bookmakers_used = {o.name: o.bookmaker for o in opp.outcomes}
    assert bookmakers_used["Team A"] == "Bookmaker One"
    assert bookmakers_used["Team B"] == "Bookmaker Two"


def test_no_arbitrage_when_margin_favors_the_book():
    event = make_event(
        "soccer_epl",
        "evt2",
        "Team A",
        "Team B",
        "2026-08-01T18:00:00Z",
        {
            "Bookmaker One": {"Team A": 1.80, "Team B": 1.90},
            "Bookmaker Two": {"Team A": 1.85, "Team B": 1.88},
        },
    )

    opportunities = find_arbitrage([event], ["h2h"], min_profit_percent=0.5, total_stake=100.0)

    assert opportunities == []


def test_respects_min_profit_threshold():
    event = make_event(
        "soccer_epl",
        "evt3",
        "Team A",
        "Team B",
        "2026-08-01T18:00:00Z",
        {
            "Bookmaker One": {"Team A": 2.02, "Team B": 1.99},
        },
    )

    opportunities = find_arbitrage([event], ["h2h"], min_profit_percent=50.0, total_stake=100.0)

    assert opportunities == []


def test_three_way_market_and_different_lines_are_kept_separate():
    event = {
        "id": "evt4",
        "sport_key": "soccer_epl",
        "home_team": "Team A",
        "away_team": "Team B",
        "commence_time": "2026-08-01T18:00:00Z",
        "bookmakers": [
            {
                "key": "book_one",
                "title": "Book One",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Team A", "price": 4.0},
                            {"name": "Draw", "price": 4.0},
                            {"name": "Team B", "price": 4.0},
                        ],
                    },
                    {
                        "key": "totals",
                        "outcomes": [
                            {"name": "Over", "point": 2.5, "price": 2.5},
                            {"name": "Under", "point": 2.5, "price": 1.5},
                            {"name": "Over", "point": 3.5, "price": 2.2},
                            {"name": "Under", "point": 3.5, "price": 2.2},
                        ],
                    },
                ],
            }
        ],
    }

    opportunities = find_arbitrage([event], ["h2h", "totals"], min_profit_percent=0.5, total_stake=100.0)

    h2h_opps = [o for o in opportunities if o.market_key == "h2h"]
    assert len(h2h_opps) == 1
    assert pytest.approx(h2h_opps[0].profit_percent, rel=1e-6) == pytest.approx(100.0 / 3.0, rel=1e-6)

    totals_opps = {o.point: o for o in opportunities if o.market_key == "totals"}
    assert 2.5 not in totals_opps
    assert 3.5 in totals_opps
