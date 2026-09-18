from datetime import date
from pathlib import Path

import pytest

from app.booking_service import (
    RecordNotFoundError,
    cancel_booking,
    create_booking,
    delete_booking,
    list_booking_history,
    list_users,
    search_hotels_by_name,
)
from app.database import initialize_database


def test_sqlite_search_preserves_part_one_hotel_matching(
    database_path: Path,
) -> None:
    matches = search_hotels_by_name(database_path, "  HARBOR lantern  ")

    assert [hotel.hotel_id for hotel in matches] == ["H001"]
    assert [stay.trip_id for stay in matches[0].available_stays] == ["T001", "T009"]
    assert search_hotels_by_name(database_path, "Ocean Palace") == []


def test_lists_demo_users_and_seeded_booking_history(database_path: Path) -> None:
    users = list_users(database_path)
    history = list_booking_history(database_path, "U001")

    assert [user.user_id for user in users] == [
        "U001",
        "U002",
        "U003",
        "U004",
        "U005",
        "U006",
    ]
    assert [booking.booking_id for booking in history] == ["B002", "B001"]
    assert history[0].status == "cancelled"
    assert history[1].stay_price_usd == 300
    assert list_booking_history(database_path, "U006") == []


def test_creates_unique_confirmed_bookings_and_allows_duplicates(
    database_path: Path,
) -> None:
    first = create_booking(
        database_path,
        "U006",
        "T001",
        booked_on=date(2026, 9, 17),
    )
    second = create_booking(
        database_path,
        "U006",
        "T001",
        booked_on=date(2026, 9, 17),
    )

    assert first.booking_id == "B007"
    assert second.booking_id == "B008"
    assert first.status == second.status == "confirmed"
    assert [booking.booking_id for booking in list_booking_history(database_path, "U006")] == [
        "B008",
        "B007",
    ]


def test_cancellation_is_idempotent_and_persists_after_reinitialization(
    database_path: Path,
) -> None:
    created = create_booking(database_path, "U006", "T001")

    first_cancellation = cancel_booking(database_path, created.booking_id)
    second_cancellation = cancel_booking(database_path, created.booking_id)
    initialize_database(database_path)
    persisted = list_booking_history(database_path, "U006")

    assert first_cancellation.status == "cancelled"
    assert second_cancellation == first_cancellation
    assert persisted[0].booking_id == created.booking_id
    assert persisted[0].status == "cancelled"


def test_deletes_only_the_created_test_booking_and_does_not_reuse_its_id(
    database_path: Path,
) -> None:
    test_booking = create_booking(database_path, "U006", "T001")

    delete_booking(database_path, test_booking.booking_id)
    initialize_database(database_path)
    replacement = create_booking(database_path, "U006", "T002")

    assert list_booking_history(database_path, "U006") == [replacement]
    assert test_booking.booking_id == "B007"
    assert replacement.booking_id == "B008"


def test_unknown_records_are_reported(database_path: Path) -> None:
    with pytest.raises(RecordNotFoundError, match="User U999 was not found"):
        create_booking(database_path, "U999", "T001")
    with pytest.raises(RecordNotFoundError, match="Trip T999 was not found"):
        create_booking(database_path, "U001", "T999")
    with pytest.raises(RecordNotFoundError, match="Booking B999 was not found"):
        cancel_booking(database_path, "B999")
    with pytest.raises(RecordNotFoundError, match="Booking B999 was not found"):
        delete_booking(database_path, "B999")
