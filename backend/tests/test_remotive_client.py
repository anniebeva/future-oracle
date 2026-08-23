import asyncio
from collections.abc import Callable

import httpx
import pytest

from app.clients.remotive import (DEFAULT_CATEGORY, RemotiveClient,
                                  RemotiveClientConnectionError,
                                  RemotiveClientHTTPError,
                                  RemotiveClientTimeoutError)
from app.core.config import Settings


def make_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused:unused@localhost:5432/unused",
        remotive_base_url="https://remotive.test/api/remote-jobs",
    )


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> RemotiveClient:
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return RemotiveClient(make_settings(), http_client)


def test_fetch_jobs_returns_raw_response_data() -> None:
    expected_payload = {
        "job-count": 1,
        "jobs": [{"id": 123, "title": "Python Developer"}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/remote-jobs"
        assert request.url.params["category"] == DEFAULT_CATEGORY
        return httpx.Response(200, json=expected_payload)

    client = make_client(handler)

    assert asyncio.run(client.fetch_jobs()) == expected_payload


def test_fetch_jobs_passes_custom_category() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["category"] == "data"
        return httpx.Response(200, json={"jobs": []})

    client = make_client(handler)

    assert asyncio.run(client.fetch_jobs(category="data")) == {"jobs": []}


def test_fetch_jobs_raises_for_http_error() -> None:
    client = make_client(lambda request: httpx.Response(503, request=request))

    with pytest.raises(RemotiveClientHTTPError, match="503"):
        asyncio.run(client.fetch_jobs())


@pytest.mark.parametrize(
    ("error", "expected_exception"),
    [
        (httpx.ReadTimeout("timed out"), RemotiveClientTimeoutError),
        (httpx.ConnectError("connection failed"), RemotiveClientConnectionError),
    ],
)
def test_fetch_jobs_raises_for_transport_errors(
    error: httpx.RequestError,
    expected_exception: type[RemotiveClientConnectionError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        error.request = request
        raise error

    client = make_client(handler)

    with pytest.raises(expected_exception):
        asyncio.run(client.fetch_jobs())
