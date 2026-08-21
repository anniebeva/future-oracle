from typing import Any

import httpx

from app.core.config import Settings

DEFAULT_CATEGORY = "software-dev"
REQUEST_TIMEOUT_SECONDS = 10.0


class RemotiveClientError(Exception):
    """Base error for the Remotive client"""


class RemotiveClientHTTPError(RemotiveClientError):
    """The Remotive API returned an error response"""


class RemotiveClientConnectionError(RemotiveClientError):
    """The Remotive API could not be reached"""


class RemotiveClientTimeoutError(RemotiveClientConnectionError):
    """The Remotive API request timed out"""


class RemotiveClient:
    """Async HTTP client for the Remotive Jobs API"""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._base_url = settings.remotive_base_url.rstrip("/")
        self._http_client = http_client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        self._owns_http_client = http_client is None

    async def fetch_jobs(self, *, category: str = DEFAULT_CATEGORY) -> dict[str, Any]:
        """Fetch source job listings for one category"""
        try:
            response = await self._http_client.get(self._base_url, params={"category": category})
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise RemotiveClientTimeoutError("The Remotive API request timed out") from error
        except httpx.HTTPStatusError as error:
            raise RemotiveClientHTTPError(
                f"The Remotive API returned HTTP {error.response.status_code}"
            ) from error
        except httpx.RequestError as error:
            raise RemotiveClientConnectionError("Could not connect to the Remotive API") from error

        return response.json()

    async def aclose(self) -> None:
        """Close the owned HTTP client"""
        if self._owns_http_client:
            await self._http_client.aclose()
