from __future__ import annotations

import argparse
import sys
import time

from dotenv import load_dotenv

from arbitrage_bot.arbitrage import find_arbitrage
from arbitrage_bot.config import load_config
from arbitrage_bot.notifier import ConsoleNotifier, FileNotifier
from arbitrage_bot.odds_client import OddsAPIClient, OddsAPIError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan bookmaker odds for arbitrage opportunities.")
    parser.add_argument("--once", action="store_true", help="Run a single scan and exit.")
    parser.add_argument("--sports", help="Comma-separated sport keys, or 'upcoming'.")
    parser.add_argument("--regions", help="Comma-separated bookmaker regions, e.g. us,uk,eu,au.")
    parser.add_argument("--markets", help="Comma-separated market keys, e.g. h2h,totals,spreads.")
    parser.add_argument("--min-profit", type=float, help="Minimum profit percent to report.")
    parser.add_argument("--stake", type=float, help="Hypothetical total stake for stake sizing.")
    parser.add_argument("--interval", type=int, help="Seconds between scans in loop mode.")
    parser.add_argument("--log-file", help="Path to append JSONL opportunity records to.")
    return parser.parse_args(argv)


def run_once(client: OddsAPIClient, config, notifiers) -> list:
    all_opportunities = []
    for sport in config.sports:
        try:
            events = client.get_odds(sport, config.regions, ",".join(config.markets))
        except OddsAPIError as exc:
            print(f"Error fetching odds for '{sport}': {exc}", file=sys.stderr)
            continue

        all_opportunities.extend(
            find_arbitrage(events, config.markets, config.min_profit_percent, config.total_stake)
        )

    for notifier in notifiers:
        notifier.notify(all_opportunities)

    return all_opportunities


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)

    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if args.sports:
        config.sports = [s.strip() for s in args.sports.split(",") if s.strip()]
    if args.regions:
        config.regions = args.regions
    if args.markets:
        config.markets = [m.strip() for m in args.markets.split(",") if m.strip()]
    if args.min_profit is not None:
        config.min_profit_percent = args.min_profit
    if args.stake is not None:
        config.total_stake = args.stake
    if args.interval is not None:
        config.poll_interval_seconds = args.interval
    if args.log_file:
        config.log_file = args.log_file

    client = OddsAPIClient(config.api_key)
    notifiers = [ConsoleNotifier(), FileNotifier(config.log_file)]

    if args.once:
        run_once(client, config, notifiers)
        return 0

    print(f"Scanning every {config.poll_interval_seconds}s. Press Ctrl+C to stop.")
    try:
        while True:
            run_once(client, config, notifiers)
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        print("Stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
