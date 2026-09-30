import pytest
from fastapi.testclient import TestClient

from app import demo_api
from app.postcode_lookup import (
    PostcodeConfigurationError,
    PostcodeLocation,
    PostcodeNotFoundError,
    PostcodeProviderError,
)


def test_demo_zip_route_calls_controller_with_requested_postcode(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_postcodes: list[str] = []

    def mocked_lookup(postcode: str) -> PostcodeLocation:
        requested_postcodes.append(postcode)
        return PostcodeLocation(
            postcode="16802",
            country_code="US",
            latitude=40.7982,
            longitude=-77.8599,
            locality="University Park",
        )

    monkeypatch.setattr(demo_api, "lookup_us_postcode", mocked_lookup)

    response = client.get(
        "/api/demo/zip-location",
        params={"postcode": "16802"},
    )

    assert response.status_code == 200
    assert requested_postcodes == ["16802"]
    assert response.json() == {
        "postcode": "16802",
        "country_code": "US",
        "latitude": 40.7982,
        "longitude": -77.8599,
        "locality": "University Park",
    }


@pytest.mark.parametrize(
    ("controller_error", "expected_status", "expected_detail"),
    [
        (
            PostcodeConfigurationError("sensitive configuration detail"),
            503,
            "Geoapify API key is not configured",
        ),
        (
            PostcodeNotFoundError("sensitive provider response"),
            404,
            "ZIP code 16802 could not be resolved",
        ),
        (
            PostcodeProviderError("sensitive provider request"),
            502,
            "Location provider request failed",
        ),
    ],
)
def test_demo_zip_route_maps_controller_errors_without_details(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    controller_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    def mocked_lookup(_: str) -> PostcodeLocation:
        raise controller_error

    monkeypatch.setattr(demo_api, "lookup_us_postcode", mocked_lookup)

    response = client.get(
        "/api/demo/zip-location",
        params={"postcode": "16802"},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert "sensitive" not in response.text


def test_demo_zip_route_requires_five_digits(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_lookup(_: str) -> PostcodeLocation:
        raise AssertionError("Controller must not receive an invalid ZIP")

    monkeypatch.setattr(demo_api, "lookup_us_postcode", unexpected_lookup)

    missing = client.get("/api/demo/zip-location")
    invalid = client.get(
        "/api/demo/zip-location",
        params={"postcode": "1680"},
    )

    assert missing.status_code == 422
    assert invalid.status_code == 422
