import pytest
from fastapi.testclient import TestClient

from app import api as api_routes
from app.nearby_hotel_search import (
    NearbyHotelPlace,
    NearbyHotelProviderError,
    NearbyHotelRateLimitError,
    NearbyHotelSearchCenter,
    NearbyHotelSearchResult,
    NoNearbyHotelsError,
)
from app.postcode_lookup import (
    PostcodeConfigurationError,
    PostcodeNotFoundError,
    PostcodeProviderError,
    PostcodeRateLimitError,
)


def test_nearby_route_returns_only_supported_fields_and_preserves_leading_zero(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def search(postcode: str) -> NearbyHotelSearchResult:
        assert postcode == "02108"
        return NearbyHotelSearchResult(
            zip="02108",
            search_center=NearbyHotelSearchCenter(
                zip="02108",
                locality="Boston",
                latitude=42.357,
                longitude=-71.063,
            ),
            hotels=[
                NearbyHotelPlace(
                    place_id="provider-place-a",
                    name=None,
                    address=None,
                    locality="Boston",
                    region="Massachusetts",
                    postcode="02108",
                    latitude=42.358,
                    longitude=-71.061,
                )
            ],
        )

    monkeypatch.setattr(api_routes, "load_nearby_hotel_places", search)

    response = client.get("/api/v1/hotels/nearby", params={"zip": "02108"})

    assert response.status_code == 200
    assert response.json() == {
        "zip": "02108",
        "search_center": {
            "zip": "02108",
            "locality": "Boston",
            "latitude": 42.357,
            "longitude": -71.063,
        },
        "count": 1,
        "hotels": [
            {
                "place_id": "provider-place-a",
                "name": None,
                "address": None,
                "locality": "Boston",
                "region": "Massachusetts",
                "postcode": "02108",
                "latitude": 42.358,
                "longitude": -71.061,
            }
        ],
    }
    assert all(
        forbidden not in response.text
        for forbidden in (
            "price",
            "nightly_rate",
            "rating",
            "availability",
            "reservation",
            "booking",
        )
    )


@pytest.mark.parametrize("value", [None, "", "2108", "0210A", "02108-1234"])
def test_nearby_route_rejects_invalid_zip_without_provider_call(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    value: str | None,
) -> None:
    def unexpected_search(_: str) -> NearbyHotelSearchResult:
        pytest.fail("invalid input must not call the provider service")

    monkeypatch.setattr(
        api_routes,
        "load_nearby_hotel_places",
        unexpected_search,
    )
    params = {} if value is None else {"zip": value}

    response = client.get("/api/v1/hotels/nearby", params=params)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_zip"


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (PostcodeNotFoundError("sensitive detail"), 404, "unresolved_zip"),
        (NoNearbyHotelsError("sensitive detail"), 404, "no_nearby_hotels"),
        (
            PostcodeConfigurationError("sensitive detail"),
            503,
            "geoapify_not_configured",
        ),
        (PostcodeProviderError("sensitive detail"), 502, "geoapify_unavailable"),
        (NearbyHotelProviderError("sensitive detail"), 502, "geoapify_unavailable"),
        (PostcodeRateLimitError("sensitive detail"), 429, "geoapify_rate_limited"),
        (NearbyHotelRateLimitError("sensitive detail"), 429, "geoapify_rate_limited"),
    ],
)
def test_nearby_route_maps_controlled_failures_to_safe_error_codes(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    def failed_search(_: str) -> NearbyHotelSearchResult:
        raise error

    monkeypatch.setattr(api_routes, "load_nearby_hotel_places", failed_search)

    response = client.get("/api/v1/hotels/nearby", params={"zip": "02108"})

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    assert "sensitive detail" not in response.text
