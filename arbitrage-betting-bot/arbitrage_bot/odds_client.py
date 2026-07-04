from __future__ import annotations

import requests

BASE_URL = "https://api.the-odds-api.com/v4"


class OddsAPIError(RuntimeError):
    pass


class OddsAPIClient:
    """Thin wrapper around the-odds-api.com v4 REST API."""

    def __init__(self, api_key: str, session: requests.Session | None = None, timeout: float = 15.0):
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout = timeout

    def list_sports(self) -> list[dict]:
        response = self.session.get(
            f"{BASE_URL}/sports",
            params={"apiKey": self.api_key},
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        return response.json()

    def get_odds(
        self,
        sport_key: str,
        regions: str,
        markets: str,
        odds_format: str = "decimal",
    ) -> list[dict]:
        response = self.session.get(
            f"{BASE_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
            },
            timeout=self.timeout,
        )
        self._raise_for_status(response)
        return response.json()

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise OddsAPIError(f"Odds API request failed ({response.status_code}): {detail}")
