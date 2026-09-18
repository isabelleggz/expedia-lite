"""Typed request and response models for the Expedia Lite API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AvailableStayResponse(BaseModel):
    """An offered stay associated with a hotel."""

    model_config = ConfigDict(from_attributes=True)

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


class HotelResponse(BaseModel):
    """A hotel and its currently offered stays."""

    model_config = ConfigDict(from_attributes=True)

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float
    available_stays: list[AvailableStayResponse]


class HotelSearchResponse(BaseModel):
    """The stable JSON envelope returned by hotel search."""

    query: str
    count: int
    hotels: list[HotelResponse]


class UserResponse(BaseModel):
    """A demo traveler available for booking."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str


class UserListResponse(BaseModel):
    """The stable JSON envelope returned for demo travelers."""

    count: int
    users: list[UserResponse]


class BookingCreateRequest(BaseModel):
    """The user and offered stay selected for a new booking."""

    user_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)


class BookingStatusUpdateRequest(BaseModel):
    """The only supported Part 2 booking status transition."""

    status: Literal["cancelled"]


class BookingResponse(BaseModel):
    """A booking enriched with its traveler, trip, and hotel details."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    user_id: str
    display_name: str
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: float
    stay_price_usd: float
    booked_on: date
    status: Literal["confirmed", "cancelled"]


class BookingHistoryResponse(BaseModel):
    """All persisted booking history for one demo traveler."""

    user_id: str
    count: int
    bookings: list[BookingResponse]
