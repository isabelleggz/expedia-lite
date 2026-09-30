"""Backend-only U.S. postcode lookup through Geoapify."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import httpx

from .config import get_geoapify_api_key


GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
REQUEST_TIMEOUT_SECONDS = 5.0


class PostcodeLookupError(RuntimeError):
    """Base error for controlled postcode lookup failures."""


class PostcodeConfigurationError(PostcodeLookupError):
    """Raised when Geoapify cannot be called without a configured key."""


class PostcodeNotFoundError(PostcodeLookupError):
    """Raised when Geoapify returns no valid match for the requested postcode."""


class PostcodeProviderError(PostcodeLookupError):
    """Raised when Geoapify cannot provide a usable response."""


class PostcodeRateLimitError(PostcodeProviderError):
    """Raised when Geoapify rate-limits the postcode request."""


@dataclass(frozen=True, slots=True)
class PostcodeLocation:
    """Small location result independent of hotel pricing data."""

    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None = None


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


def _matching_location(
    result: Any,
    requested_postcode: str,
) -> PostcodeLocation | None:
    if not isinstance(result, dict):
        return None
    if str(result.get("postcode", "")).strip() != requested_postcode:
        return None
    if str(result.get("country_code", "")).strip().casefold() != "us":
        return None

    latitude = _valid_coordinate(result.get("lat"), -90.0, 90.0)
    longitude = _valid_coordinate(result.get("lon"), -180.0, 180.0)
    if latitude is None or longitude is None:
        return None

    locality = next(
        (
            value.strip()
            for field in ("city", "town", "village", "municipality")
            if isinstance((value := result.get(field)), str) and value.strip()
        ),
        None,
    )
    return PostcodeLocation(
        postcode=requested_postcode,
        country_code="US",
        latitude=latitude,
        longitude=longitude,
        locality=locality,
    )


def lookup_us_postcode(
    postcode: str,
    *,
    client: httpx.Client | None = None,
) -> PostcodeLocation:
    """Resolve a U.S. postcode or raise a controlled lookup error.

    ``PostcodeNotFoundError`` means the provider returned no exact U.S. match
    with valid coordinates. ``PostcodeProviderError`` means the provider
    request or response failed. The API key is never included in either error.
    """

    requested_postcode = postcode.strip()
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise PostcodeConfigurationError("Geoapify API key is not configured")

    owns_client = client is None
    http_client = client or httpx.Client()
    try:
        try:
            response = http_client.get(
                GEOAPIFY_GEOCODE_URL,
                params={
                    "postcode": requested_postcode,
                    "type": "postcode",
                    "filter": "countrycode:us",
                    "format": "json",
                    "limit": 5,
                    "apiKey": api_key,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 429:
                raise PostcodeRateLimitError(
                    "Geoapify postcode lookup was rate-limited"
                )
            response.raise_for_status()
            payload = response.json()
        except PostcodeRateLimitError:
            raise
        except (httpx.HTTPError, ValueError, TypeError):
            raise PostcodeProviderError("Geoapify postcode lookup failed") from None
    finally:
        if owns_client:
            http_client.close()

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise PostcodeProviderError("Geoapify postcode lookup failed")

    for result in payload["results"]:
        location = _matching_location(result, requested_postcode)
        if location is not None:
            return location

    raise PostcodeNotFoundError(
        f"No matching U.S. location was found for postcode {requested_postcode}"
    )
