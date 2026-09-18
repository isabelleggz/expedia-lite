"""Thin FastAPI routes for hotel search and persisted bookings."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

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
from .schemas import (
    BookingCreateRequest,
    BookingHistoryResponse,
    BookingResponse,
    BookingStatusUpdateRequest,
    HotelResponse,
    HotelSearchResponse,
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
