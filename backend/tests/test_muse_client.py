from collections.abc import Callable

import httpx
import pytest

from app.clients.muse_client import (DEFAULT_CATEGORY, MuseClient,
                                     MuseClientConnectionError,
                                     MuseClientHTTPError,
                                     MuseClientTimeoutError)
from app.core.config import Settings


def make_settings(api_key: str | None = None) -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused:unused@localhost:5432/unused",
        muse_base_url="https://muse.test/api/public",
        muse_api_key=api_key,
    )


def make_client(
    handler: Callable[[httpx.Request], httpx.Response], api_key: str | None = None
) -> MuseClient:
    return MuseClient(
        make_settings(api_key),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_fetch_jobs_returns_raw_response_data() -> None:
    expected_payload = {"page": 0, "results": [{"id": 123, "name": "Python Developer"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(
            "https://muse.test/api/public/jobs?page=0&limit=20&category=Software+Engineering"
        )
        return httpx.Response(200, json=expected_payload)

    client = make_client(handler)

    assert client.fetch_jobs() == expected_payload


def test_fetch_jobs_passes_pagination_and_location_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["page"] == "3"
        assert request.url.params["limit"] == "50"
        assert request.url.params["category"] == "Computer and IT"
        assert request.url.params["location"] == "New York, NY"
        return httpx.Response(200, json={"results": []})

    client = make_client(handler)

    assert client.fetch_jobs(
        page=3,
        limit=50,
        category="Computer and IT",
        location="New York, NY",
    ) == {"results": []}


def test_fetch_jobs_includes_configured_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(200, json={"results": []})

    client = make_client(handler, api_key="test-key")

    client.fetch_jobs()


def test_fetch_jobs_works_without_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key" not in request.url.params
        assert request.url.params["category"] == DEFAULT_CATEGORY
        return httpx.Response(200, json={"results": []})

    client = make_client(handler)

    client.fetch_jobs()


def test_fetch_jobs_raises_for_http_error() -> None:
    client = make_client(lambda request: httpx.Response(429, request=request))

    with pytest.raises(MuseClientHTTPError, match="429"):
        client.fetch_jobs()


@pytest.mark.parametrize(
    ("error", "expected_exception"),
    [
        (httpx.ReadTimeout("timed out"), MuseClientTimeoutError),
        (httpx.ConnectError("connection failed"), MuseClientConnectionError),
    ],
)
def test_fetch_jobs_raises_for_transport_errors(
    error: httpx.RequestError,
    expected_exception: type[MuseClientConnectionError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        error.request = request
        raise error

    client = make_client(handler)

    with pytest.raises(expected_exception):
        client.fetch_jobs()
