"""FastAPI routes and response models for hotel search."""

from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from .hotel_search import (
    connect_records_by_hotel_id,
    find_matching_hotels_by_name,
    load_available_stay_records,
    load_hotel_records,
)


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"


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


hotels = load_hotel_records(DATA_DIRECTORY / "hotels.csv")
available_stays = load_available_stay_records(DATA_DIRECTORY / "trips.csv")
connected_hotels = connect_records_by_hotel_id(hotels, available_stays)

router = APIRouter(prefix="/api/v1")


@router.get("/hotels/search", response_model=HotelSearchResponse)
def search_hotels(
    hotel_name: Annotated[
        str,
        Query(description="Whole or partial hotel name; matching ignores case"),
    ],
) -> HotelSearchResponse:
    """Return hotels matching a name along with their offered stays."""

    matches = find_matching_hotels_by_name(hotel_name, connected_hotels)
    return HotelSearchResponse(
        query=hotel_name,
        count=len(matches),
        hotels=[HotelResponse.model_validate(hotel) for hotel in matches],
    )
