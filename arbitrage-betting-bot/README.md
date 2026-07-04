# Arbitrage Betting Bot

Scans bookmaker odds across regions/books via [the-odds-api.com](https://the-odds-api.com/)
and flags **sports arbitrage** opportunities: situations where the best available prices
across different bookmakers guarantee a profit no matter which outcome wins.

This tool only **scans and reports**. It does not place bets or interact with any
bookmaker account.

## How it works

For a market with mutually exclusive outcomes (e.g. Team A / Team B, or Home / Draw / Away),
take the best available decimal price for each outcome across all scanned bookmakers.
If the sum of the implied probabilities (`1 / price`) is less than 1, betting a
proportional stake on every outcome guarantees the same payout regardless of the result:

```
stake_i = total_stake * (1 / price_i) / sum(1 / price_j for all outcomes j)
profit_percent = (1 / sum(1 / price_j) - 1) * 100
```

## Setup

```bash
cd arbitrage-betting-bot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# edit .env and set ODDS_API_KEY (free tier at https://the-odds-api.com/)
```

## Usage

```bash
# one-off scan
arbitrage-bot --once

# continuous scan, polling every 5 minutes (or POLL_INTERVAL_SECONDS in .env)
arbitrage-bot
```

Useful flags (all override the corresponding `.env` value for that run):

| Flag | Description |
| --- | --- |
| `--once` | Run a single scan and exit. |
| `--sports` | Comma-separated sport keys, or `upcoming`. |
| `--regions` | Comma-separated bookmaker regions, e.g. `us,uk,eu,au`. |
| `--markets` | Comma-separated market keys, e.g. `h2h,totals,spreads`. |
| `--min-profit` | Minimum guaranteed profit percent to report. |
| `--stake` | Hypothetical total stake used for the stake split. |
| `--interval` | Seconds between scans in loop mode. |
| `--log-file` | Path to append found opportunities to as JSON lines. |

Found opportunities are printed to the console and appended to `LOG_FILE` (default
`arbitrage_log.jsonl`) as JSON lines for later analysis.

## Running tests

```bash
pytest
```

## Disclaimer

This project is for informational and educational purposes. Arbitrage (or "arbing")
across bookmakers may violate individual bookmakers' terms of service and can lead to
limited stakes or closed accounts. Sports betting is also regulated differently by
jurisdiction, and may be restricted or illegal where you live. You are responsible for
complying with local laws and each bookmaker's terms before acting on anything this
tool reports. Odds change quickly; by the time you place a bet, a reported opportunity
may no longer exist.
