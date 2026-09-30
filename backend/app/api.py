"""Thin FastAPI routes for hotel search and persisted bookings."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .booking_service import (
    InvalidBookingError,
    RecordNotFoundError,
    cancel_booking as cancel_stored_booking,
    create_booking as create_stored_booking,
    delete_booking as delete_stored_booking,
    list_booking_history as load_booking_history,
    list_users as load_users,
    search_hotels_by_name,
)
from .nearby_hotel_search import (
    NearbyHotelProviderError,
    NearbyHotelRateLimitError,
    NoNearbyHotelsError,
    search_nearby_hotel_places as load_nearby_hotel_places,
)
from .postcode_lookup import (
    PostcodeConfigurationError,
    PostcodeNotFoundError,
    PostcodeProviderError,
    PostcodeRateLimitError,
)
from .schemas import (
    ApiErrorDetail,
    ApiErrorResponse,
    BookingCreateRequest,
    BookingHistoryResponse,
    BookingResponse,
    BookingStatusUpdateRequest,
    HotelResponse,
    HotelSearchResponse,
    NearbyHotelErrorCode,
    NearbyHotelPlaceResponse,
    NearbyHotelSearchCenterResponse,
    NearbyHotelSearchQuery,
    NearbyHotelSearchResponse,
    UserListResponse,
    UserResponse,
)


router = APIRouter(prefix="/api/v1")


def _database_path(request: Request) -> Path:
    return Path(request.app.state.database_path)


def _not_found(error: RecordNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


def _invalid_booking(error: InvalidBookingError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(error),
    )


def _nearby_search_error(
    status_code: int,
    code: NearbyHotelErrorCode,
    message: str,
) -> JSONResponse:
    payload = ApiErrorResponse(error=ApiErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.get("/hotels/search", response_model=HotelSearchResponse)
def search_hotels(
    request: Request,
    hotel_name: Annotated[
        str,
        Query(description="Whole or partial hotel name; matching ignores case"),
    ],
) -> HotelSearchResponse:
    """Return SQLite-backed hotel matches and their offered stays."""

    matches = search_hotels_by_name(_database_path(request), hotel_name)
    return HotelSearchResponse(
        query=hotel_name,
        count=len(matches),
        hotels=[HotelResponse.model_validate(hotel) for hotel in matches],
    )


@router.get(
    "/hotels/nearby",
    response_model=NearbyHotelSearchResponse,
    responses={
        400: {"model": ApiErrorResponse, "description": "Invalid ZIP input"},
        404: {
            "model": ApiErrorResponse,
            "description": "Unresolved ZIP or no nearby hotel places",
        },
        429: {
            "model": ApiErrorResponse,
            "description": "Geoapify quota or rate limit reached",
        },
        502: {
            "model": ApiErrorResponse,
            "description": "Geoapify request or response failure",
        },
        503: {
            "model": ApiErrorResponse,
            "description": "Geoapify is not configured",
        },
    },
)
def search_nearby_hotels(
    zip_code: Annotated[
        str | None,
        Query(
            alias="zip",
            description="Exact five-digit U.S. ZIP code",
        ),
    ] = None,
) -> NearbyHotelSearchResponse | JSONResponse:
    """Return Geoapify hotel places within 5 km of an exact U.S. ZIP."""

    try:
        query = NearbyHotelSearchQuery.model_validate({"zip": zip_code})
    except ValidationError:
        return _nearby_search_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_zip",
            "Enter a five-digit U.S. ZIP code.",
        )

    try:
        result = load_nearby_hotel_places(query.zip)
    except PostcodeConfigurationError:
        return _nearby_search_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "geoapify_not_configured",
            "Location search is not configured yet.",
        )
    except PostcodeNotFoundError:
        return _nearby_search_error(
            status.HTTP_404_NOT_FOUND,
            "unresolved_zip",
            "We could not resolve that exact U.S. ZIP code.",
        )
    except NoNearbyHotelsError:
        return _nearby_search_error(
            status.HTTP_404_NOT_FOUND,
            "no_nearby_hotels",
            "No hotel places were returned within 5 km of that ZIP code.",
        )
    except (PostcodeRateLimitError, NearbyHotelRateLimitError):
        return _nearby_search_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "geoapify_rate_limited",
            "Location search is temporarily rate-limited. Please try again later.",
        )
    except (PostcodeProviderError, NearbyHotelProviderError):
        return _nearby_search_error(
            status.HTTP_502_BAD_GATEWAY,
            "geoapify_unavailable",
            "Location search is temporarily unavailable. Please try again.",
        )

    return NearbyHotelSearchResponse(
        zip=result.zip,
        search_center=NearbyHotelSearchCenterResponse.model_validate(
            result.search_center
        ),
        count=len(result.hotels),
        hotels=[
            NearbyHotelPlaceResponse.model_validate(hotel) for hotel in result.hotels
        ],
    )


@router.get("/users", response_model=UserListResponse)
def list_users(request: Request) -> UserListResponse:
    """Return the demo travelers available for booking."""

    users = load_users(_database_path(request))
    return UserListResponse(
        count=len(users),
        users=[UserResponse.model_validate(user) for user in users],
    )


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    request: Request,
    booking_request: BookingCreateRequest,
) -> BookingResponse:
    """Create and return a persisted confirmed booking."""

    try:
        booking = create_stored_booking(
            _database_path(request),
            booking_request.user_id,
            booking_request.trip_id,
        )
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except InvalidBookingError as error:
        raise _invalid_booking(error) from error
    return BookingResponse.model_validate(booking)


@router.get(
    "/users/{user_id}/bookings",
    response_model=BookingHistoryResponse,
)
def get_booking_history(
    request: Request,
    user_id: str,
) -> BookingHistoryResponse:
    """Return confirmed and cancelled booking history for one traveler."""

    try:
        bookings = load_booking_history(_database_path(request), user_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except InvalidBookingError as error:
        raise _invalid_booking(error) from error
    return BookingHistoryResponse(
        user_id=user_id,
        count=len(bookings),
        bookings=[BookingResponse.model_validate(booking) for booking in bookings],
    )


@router.patch(
    "/bookings/{booking_id}",
    response_model=BookingResponse,
)
def cancel_booking(
    request: Request,
    booking_id: str,
    booking_update: BookingStatusUpdateRequest,
) -> BookingResponse:
    """Idempotently update one booking's status to cancelled."""

    del booking_update
    try:
        booking = cancel_stored_booking(_database_path(request), booking_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except InvalidBookingError as error:
        raise _invalid_booking(error) from error
    return BookingResponse.model_validate(booking)


@router.delete(
    "/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_booking(request: Request, booking_id: str) -> Response:
    """Permanently remove one booking."""

    try:
        delete_stored_booking(_database_path(request), booking_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except InvalidBookingError as error:
        raise _invalid_booking(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
