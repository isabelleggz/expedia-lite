import httpx
import pytest

from app import nearby_hotel_search, postcode_lookup
from app.nearby_hotel_search import (
    NearbyHotelProviderError,
    NearbyHotelRateLimitError,
    NoNearbyHotelsError,
    find_nearby_hotel_places,
    search_nearby_hotel_places,
)
from app.postcode_lookup import (
    PostcodeConfigurationError,
    PostcodeLocation,
    PostcodeNotFoundError,
)


TEST_API_KEY = "not-a-real-key"
CENTER = PostcodeLocation(
    postcode="02108",
    country_code="US",
    latitude=42.357,
    longitude=-71.063,
    locality="Boston",
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _configure_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        postcode_lookup,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )
    monkeypatch.setattr(
        nearby_hotel_search,
        "get_geoapify_api_key",
        lambda: TEST_API_KEY,
    )


def test_search_preserves_leading_zero_and_uses_exact_five_kilometer_center(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_key(monkeypatch)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/geocode/search":
            assert request.url.params["postcode"] == "02108"
            assert request.url.params["type"] == "postcode"
            assert request.url.params["filter"] == "countrycode:us"
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

        assert request.url.path == "/v2/places"
        assert request.url.params["categories"] == "accommodation.hotel"
        assert request.url.params["filter"] == "circle:-71.063,42.357,5000"
        assert request.url.params["bias"] == "proximity:-71.063,42.357"
        assert request.url.params["limit"] == "20"
        assert request.url.params["lang"] == "en"
        assert request.url.params["apiKey"] == TEST_API_KEY
        assert all(
            timeout == postcode_lookup.REQUEST_TIMEOUT_SECONDS
            for timeout in request.extensions["timeout"].values()
        )
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {
                            "place_id": "provider-place-a",
                            "name": "Provider supplied name",
                            "formatted": "Provider supplied address",
                            "city": "Boston",
                            "state": "Massachusetts",
                            "postcode": "02108",
                            "country_code": "us",
                            "lat": 42.358,
                            "lon": -71.061,
                            "price": "$999",
                            "rating": 5,
                            "availability": "available",
                            "reservation": "confirmed",
                        }
                    },
                    {
                        "properties": {
                            "place_id": "provider-place-b",
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-71.06, 42.359],
                        },
                    },
                    {
                        "properties": {
                            "place_id": "provider-place-a",
                            "country_code": "us",
                            "lat": 42.36,
                            "lon": -71.059,
                        }
                    },
                ]
            },
        )

    with _client(handler) as client:
        result = search_nearby_hotel_places("02108", client=client)

    assert len(requests) == 2
    assert result.zip == "02108"
    assert result.search_center.zip == "02108"
    assert result.search_center.latitude == 42.357
    assert result.search_center.longitude == -71.063
    assert [hotel.place_id for hotel in result.hotels] == [
        "provider-place-a",
        "provider-place-b",
    ]
    assert result.hotels[1].name is None
    assert result.hotels[1].address is None
    assert result.hotels[1].locality is None
    assert result.hotels[1].region is None
    assert result.hotels[1].postcode is None
    assert all(
        not hasattr(result.hotels[0], field)
        for field in (
            "price",
            "nightly_rate",
            "rating",
            "availability",
            "reservation",
            "booking",
        )
    )


def test_unresolved_exact_zip_never_calls_places(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_key(monkeypatch)
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        assert request.url.path == "/v1/geocode/search"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "postcode": "02109",
                        "country_code": "us",
                        "lat": 42.36,
                        "lon": -71.05,
                    }
                ]
            },
        )

    with _client(handler) as client:
        with pytest.raises(PostcodeNotFoundError):
            search_nearby_hotel_places("02108", client=client)

    assert requested_paths == ["/v1/geocode/search"]


def test_places_reports_no_usable_nearby_hotels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_key(monkeypatch)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {
                            "name": "No provider ID",
                            "lat": 42.358,
                            "lon": -71.061,
                        }
                    },
                    {
                        "properties": {
                            "place_id": "no-provider-coordinates",
                            "name": "No provider coordinates",
                        }
                    },
                ]
            },
        )

    with _client(handler) as client:
        with pytest.raises(NoNearbyHotelsError):
            find_nearby_hotel_places(CENTER, client=client)


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: (_ for _ in ()).throw(
            httpx.ConnectError("network unavailable", request=request)
        ),
        lambda _: httpx.Response(200, json={"unexpected": []}),
        lambda _: httpx.Response(200, content=b"not-json"),
    ],
    ids=["network", "invalid-shape", "invalid-json"],
)
def test_places_sanitizes_provider_and_invalid_response_failures(
    monkeypatch: pytest.MonkeyPatch,
    handler,
) -> None:
    _configure_key(monkeypatch)

    with _client(handler) as client:
        with pytest.raises(
            NearbyHotelProviderError,
            match="^Geoapify Places (request failed|returned invalid data)$",
        ) as error:
            find_nearby_hotel_places(CENTER, client=client)

    assert TEST_API_KEY not in str(error.value)


def test_places_distinguishes_provider_rate_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_key(monkeypatch)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text=f"quota for {TEST_API_KEY}")

    with _client(handler) as client:
        with pytest.raises(NearbyHotelRateLimitError) as error:
            find_nearby_hotel_places(CENTER, client=client)

    assert TEST_API_KEY not in str(error.value)


def test_places_requires_server_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        nearby_hotel_search,
        "get_geoapify_api_key",
        lambda: None,
    )

    with pytest.raises(PostcodeConfigurationError):
        find_nearby_hotel_places(CENTER)
