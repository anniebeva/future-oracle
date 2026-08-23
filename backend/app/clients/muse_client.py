from typing import Any

import httpx

from app.core.config import Settings

DEFAULT_CATEGORY = "Software Engineering"
REQUEST_TIMEOUT_SECONDS = 10.0


class MuseClientError(Exception):
    """Base error for The Muse client"""


class MuseClientHTTPError(MuseClientError):
    """The Muse API returned an error response"""


class MuseClientConnectionError(MuseClientError):
    """The Muse API could not be reached"""


class MuseClientTimeoutError(MuseClientConnectionError):
    """The Muse API request timed out"""


class MuseClient:
    """HTTP client for The Muse Jobs API"""

    def __init__(
        self, settings: Settings, http_client: httpx.Client | None = None
    ) -> None:
        self._base_url = settings.muse_base_url.rstrip("/")
        self._api_key = settings.muse_api_key
        self._http_client = http_client or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
        self._owns_http_client = http_client is None

    def fetch_jobs(
        self,
        *,
        page: int = 0,
        limit: int = 20,
        category: str = DEFAULT_CATEGORY,
        location: str | None = None,
    ) -> dict[str, Any]:
        """Fetch one page of source job listings"""
        params: dict[str, str | int] = {
            "page": page,
            "limit": limit,
            "category": category,
        }
        if location is not None:
            params["location"] = location
        if self._api_key:
            params["api_key"] = self._api_key

        try:
            response = self._http_client.get(f"{self._base_url}/jobs", params=params)
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise MuseClientTimeoutError("The Muse API request timed out") from error
        except httpx.HTTPStatusError as error:
            raise MuseClientHTTPError(
                f"The Muse API returned HTTP {error.response.status_code}"
            ) from error
        except httpx.RequestError as error:
            raise MuseClientConnectionError(
                "Could not connect to The Muse API"
            ) from error

        return response.json()

    def close(self) -> None:
        """Close the owned HTTP client"""
        if self._owns_http_client:
            self._http_client.close()
