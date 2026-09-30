"""Geoapify Places search centered on an exact U.S. postcode result."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import httpx

from .config import get_geoapify_api_key
from .postcode_lookup import (
    REQUEST_TIMEOUT_SECONDS,
    PostcodeConfigurationError,
    PostcodeLocation,
    lookup_us_postcode,
)


GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
HOTEL_CATEGORY = "accommodation.hotel"
SEARCH_RADIUS_METERS = 5_000
PLACES_LIMIT = 20


class NearbyHotelSearchError(RuntimeError):
    """Base error for controlled nearby-hotel search failures."""


class NoNearbyHotelsError(NearbyHotelSearchError):
    """Raised when a resolved postcode has no usable nearby hotel places."""


class NearbyHotelProviderError(NearbyHotelSearchError):
    """Raised when Geoapify Places cannot provide a usable response."""


class NearbyHotelRateLimitError(NearbyHotelSearchError):
    """Raised when Geoapify rate-limits the Places request."""


@dataclass(frozen=True, slots=True)
class NearbyHotelSearchCenter:
    """Exact U.S. postcode coordinates used as the Places search origin."""

    zip: str
    locality: str | None
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class NearbyHotelPlace:
    """Truthful subset of one provider hotel-place feature."""

    place_id: str
    name: str | None
    address: str | None
    locality: str | None
    region: str | None
    postcode: str | None
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class NearbyHotelSearchResult:
    """Normalized center and hotel places for one ZIP search."""

    zip: str
    search_center: NearbyHotelSearchCenter
    hotels: list[NearbyHotelPlace]


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _valid_coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
        return None
    return coordinate


def _feature_coordinates(
    properties: dict[str, Any],
    geometry: Any,
) -> tuple[float, float] | None:
    latitude = _valid_coordinate(properties.get("lat"), -90.0, 90.0)
    longitude = _valid_coordinate(properties.get("lon"), -180.0, 180.0)
    if latitude is not None and longitude is not None:
        return latitude, longitude

    if not isinstance(geometry, dict):
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    longitude = _valid_coordinate(coordinates[0], -180.0, 180.0)
    latitude = _valid_coordinate(coordinates[1], -90.0, 90.0)
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


def _hotel_from_feature(feature: Any) -> NearbyHotelPlace | None:
    if not isinstance(feature, dict):
        raise NearbyHotelProviderError("Geoapify Places returned invalid data")
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise NearbyHotelProviderError("Geoapify Places returned invalid data")

    place_id = _optional_text(properties.get("place_id"))
    coordinates = _feature_coordinates(properties, feature.get("geometry"))
    if place_id is None or coordinates is None:
        return None

    locality = next(
        (
            text
            for field in ("city", "town", "village", "municipality")
            if (text := _optional_text(properties.get(field))) is not None
        ),
        None,
    )
    latitude, longitude = coordinates
    return NearbyHotelPlace(
        place_id=place_id,
        name=_optional_text(properties.get("name")),
        address=_optional_text(properties.get("formatted")),
        locality=locality,
        region=_optional_text(properties.get("state")),
        postcode=_optional_text(properties.get("postcode")),
        latitude=latitude,
        longitude=longitude,
    )


def find_nearby_hotel_places(
    center: PostcodeLocation,
    *,
    client: httpx.Client | None = None,
) -> list[NearbyHotelPlace]:
    """Return normalized hotel places within 5 km of a U.S. postcode center."""

    api_key = get_geoapify_api_key()
    if api_key is None:
        raise PostcodeConfigurationError("Geoapify API key is not configured")

    owns_client = client is None
    http_client = client or httpx.Client()
    try:
        try:
            response = http_client.get(
                GEOAPIFY_PLACES_URL,
                params={
                    "categories": HOTEL_CATEGORY,
                    "filter": (
                        f"circle:{center.longitude},{center.latitude},"
                        f"{SEARCH_RADIUS_METERS}"
                    ),
                    "bias": f"proximity:{center.longitude},{center.latitude}",
                    "limit": PLACES_LIMIT,
                    "lang": "en",
                    "apiKey": api_key,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 429:
                raise NearbyHotelRateLimitError(
                    "Geoapify Places request was rate-limited"
                )
            response.raise_for_status()
            payload = response.json()
        except NearbyHotelRateLimitError:
            raise
        except (httpx.HTTPError, ValueError, TypeError):
            raise NearbyHotelProviderError(
                "Geoapify Places request failed"
            ) from None
    finally:
        if owns_client:
            http_client.close()

    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise NearbyHotelProviderError("Geoapify Places returned invalid data")

    hotels_by_id: dict[str, NearbyHotelPlace] = {}
    for feature in payload["features"]:
        hotel = _hotel_from_feature(feature)
        if hotel is not None:
            hotels_by_id.setdefault(hotel.place_id, hotel)

    if not hotels_by_id:
        raise NoNearbyHotelsError(
            f"No hotel places were returned within 5 km of ZIP {center.postcode}"
        )
    return list(hotels_by_id.values())


def search_nearby_hotel_places(
    postcode: str,
    *,
    client: httpx.Client | None = None,
) -> NearbyHotelSearchResult:
    """Resolve an exact U.S. ZIP, then find provider hotel places around it."""

    owns_client = client is None
    http_client = client or httpx.Client()
    try:
        location = lookup_us_postcode(postcode, client=http_client)
        hotels = find_nearby_hotel_places(location, client=http_client)
    finally:
        if owns_client:
            http_client.close()

    return NearbyHotelSearchResult(
        zip=location.postcode,
        search_center=NearbyHotelSearchCenter(
            zip=location.postcode,
            locality=location.locality,
            latitude=location.latitude,
            longitude=location.longitude,
        ),
        hotels=hotels,
    )
