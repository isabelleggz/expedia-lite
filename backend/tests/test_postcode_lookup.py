import httpx
import pytest

from app import postcode_lookup
from app.postcode_lookup import (
    PostcodeLocation,
    PostcodeNotFoundError,
    PostcodeProviderError,
    PostcodeRateLimitError,
    lookup_us_postcode,
)


TEST_API_KEY = "not-a-real-key"


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_lookup_returns_exact_us_postcode_with_valid_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postcode_lookup,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["postcode"] == "02108"
        assert request.url.params["type"] == "postcode"
        assert request.url.params["filter"] == "countrycode:us"
        assert request.url.params["format"] == "json"
        assert request.url.params["limit"] == "5"
        assert request.url.params["apiKey"] == TEST_API_KEY
        assert all(
            timeout == postcode_lookup.REQUEST_TIMEOUT_SECONDS
            for timeout in request.extensions["timeout"].values()
        )
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "02108",
                        "country_code": "us",
                        "lat": 42.357,
                        "lon": -71.063,
                        "city": "Boston",
                    }
                ]
            },
        )

    with _client(handler) as client:
        location = lookup_us_postcode("02108", client=client)

    assert location == PostcodeLocation(
        postcode="02108",
        country_code="US",
        latitude=42.357,
        longitude=-71.063,
        locality="Boston",
    )


def test_lookup_rejects_mismatched_locations_and_invalid_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postcode_lookup,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "16802",
                        "country_code": "ca",
                        "lat": 40.7982,
                        "lon": -77.8599,
                    },
                    {
                        "postcode": "16801",
                        "country_code": "us",
                        "lat": 40.7982,
                        "lon": -77.8599,
                    },
                    {
                        "postcode": "16802",
                        "country_code": "us",
                        "lat": "invalid",
                        "lon": -77.8599,
                    },
                ]
            },
        )

    with _client(handler) as client:
        with pytest.raises(PostcodeNotFoundError, match="No matching U.S. location"):
            lookup_us_postcode("16802", client=client)


def test_lookup_sanitizes_provider_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postcode_lookup,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="provider unavailable")

    with _client(handler) as client:
        with pytest.raises(
            PostcodeProviderError,
            match="^Geoapify postcode lookup failed$",
        ) as error:
            lookup_us_postcode("16802", client=client)

    assert TEST_API_KEY not in str(error.value)


def test_lookup_distinguishes_provider_rate_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postcode_lookup,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text=f"quota for {TEST_API_KEY}")

    with _client(handler) as client:
        with pytest.raises(PostcodeRateLimitError) as error:
            lookup_us_postcode("02108", client=client)

    assert TEST_API_KEY not in str(error.value)
