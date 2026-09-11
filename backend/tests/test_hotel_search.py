from datetime import date
from decimal import Decimal
from pathlib import Path

from app.hotel_search import (
    AvailableStayRecord,
    HotelRecord,
    HotelWithAvailableStays,
    connect_records_by_hotel_id,
    find_matching_hotels_by_name,
    load_available_stay_records,
    load_hotel_records,
)


DATA_DIRECTORY = Path(__file__).parent.parent / "data"


def load_connected_records() -> tuple[
    list[HotelRecord],
    list[AvailableStayRecord],
    list[HotelWithAvailableStays],
]:
    hotels = load_hotel_records(DATA_DIRECTORY / "hotels.csv")
    available_stays = load_available_stay_records(DATA_DIRECTORY / "trips.csv")
    return hotels, available_stays, connect_records_by_hotel_id(hotels, available_stays)


def test_loads_hotel_records() -> None:
    hotels = load_hotel_records(DATA_DIRECTORY / "hotels.csv")

    assert len(hotels) == 8
    assert hotels[0].hotel_id == "H001"
    assert hotels[0].hotel_name == "Harbor Lantern Hotel"
    assert hotels[0].nightly_rate_usd == Decimal("150")


def test_loads_available_stay_records() -> None:
    stays = load_available_stay_records(DATA_DIRECTORY / "trips.csv")

    assert len(stays) == 12
    assert stays[0].trip_id == "T001"
    assert stays[0].hotel_id == "H001"
    assert stays[0].check_in == date(2026, 9, 18)
    assert stays[0].check_out == date(2026, 9, 20)


def test_connects_each_hotel_to_its_available_stays() -> None:
    _, available_stays, connected_hotels = load_connected_records()

    connected_stay_ids = {
        stay.trip_id
        for hotel in connected_hotels
        for stay in hotel.available_stays
    }

    assert len(connected_hotels) == 8
    assert connected_stay_ids == {stay.trip_id for stay in available_stays}


def test_finds_hotel_by_partial_name_with_available_stays() -> None:
    _, _, connected_hotels = load_connected_records()

    matches = find_matching_hotels_by_name("  HARBOR lantern  ", connected_hotels)

    assert [hotel.hotel_id for hotel in matches] == ["H001"]
    assert [stay.trip_id for stay in matches[0].available_stays] == ["T001", "T009"]


def test_no_matching_hotel_returns_empty_list() -> None:
    _, _, connected_hotels = load_connected_records()

    assert find_matching_hotels_by_name("Ocean Palace", connected_hotels) == []


def test_blank_hotel_name_returns_empty_list() -> None:
    _, _, connected_hotels = load_connected_records()

    assert find_matching_hotels_by_name("   ", connected_hotels) == []
