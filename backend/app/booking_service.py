"""Framework-independent hotel search and booking operations over SQLite."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .database import open_database
from .hotel_search import (
    AvailableStayRecord,
    HotelRecord,
    HotelWithAvailableStays,
    connect_records_by_hotel_id,
    find_matching_hotels_by_name,
)


class RecordNotFoundError(LookupError):
    """Raised when an operation references an unknown stored record."""


class InvalidBookingError(ValueError):
    """Raised when booking input is blank or otherwise invalid."""


@dataclass(frozen=True, slots=True)
class UserRecord:
    """A selectable demo traveler."""

    user_id: str
    display_name: str


@dataclass(frozen=True, slots=True)
class BookingRecord:
    """A booking joined to its traveler, trip, and hotel details."""

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
    nightly_rate_usd: Decimal
    booked_on: date
    status: str

    @property
    def nights(self) -> int:
        """Return the number of overnight stays in the trip."""

        return (self.check_out - self.check_in).days

    @property
    def stay_price_usd(self) -> Decimal:
        """Return the trip price derived from nights and nightly rate."""

        return self.nightly_rate_usd * self.nights


BOOKING_SELECT_SQL = """
SELECT
    bookings.booking_id,
    bookings.user_id,
    users.display_name,
    bookings.trip_id,
    trips.trip_name,
    hotels.hotel_id,
    hotels.hotel_name,
    hotels.city,
    hotels.state,
    trips.check_in,
    trips.check_out,
    hotels.nightly_rate_usd,
    bookings.booked_on,
    bookings.status
FROM bookings
JOIN users ON users.user_id = bookings.user_id
JOIN trips ON trips.trip_id = bookings.trip_id
JOIN hotels ON hotels.hotel_id = trips.hotel_id
"""


def _booking_from_row(row: sqlite3.Row) -> BookingRecord:
    return BookingRecord(
        booking_id=row["booking_id"],
        user_id=row["user_id"],
        display_name=row["display_name"],
        trip_id=row["trip_id"],
        trip_name=row["trip_name"],
        hotel_id=row["hotel_id"],
        hotel_name=row["hotel_name"],
        city=row["city"],
        state=row["state"],
        check_in=date.fromisoformat(row["check_in"]),
        check_out=date.fromisoformat(row["check_out"]),
        nightly_rate_usd=Decimal(str(row["nightly_rate_usd"])),
        booked_on=date.fromisoformat(row["booked_on"]),
        status=row["status"],
    )


def _get_booking(
    connection: sqlite3.Connection,
    booking_id: str,
) -> BookingRecord:
    row = connection.execute(
        f"{BOOKING_SELECT_SQL} WHERE bookings.booking_id = ?",
        (booking_id,),
    ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"Booking {booking_id} was not found")
    return _booking_from_row(row)


def search_hotels_by_name(
    database_path: str | Path,
    hotel_name: str,
) -> list[HotelWithAvailableStays]:
    """Load hotel and stay records from SQLite and apply Part 1 name matching."""

    with open_database(database_path) as connection:
        hotel_rows = connection.execute(
            """
            SELECT hotel_id, hotel_name, city, state, nightly_rate_usd
            FROM hotels
            ORDER BY hotel_id
            """
        ).fetchall()
        trip_rows = connection.execute(
            """
            SELECT trip_id, hotel_id, trip_name, check_in, check_out
            FROM trips
            ORDER BY trip_id
            """
        ).fetchall()

    hotels = [
        HotelRecord(
            hotel_id=row["hotel_id"],
            hotel_name=row["hotel_name"],
            city=row["city"],
            state=row["state"],
            nightly_rate_usd=Decimal(str(row["nightly_rate_usd"])),
        )
        for row in hotel_rows
    ]
    stays = [
        AvailableStayRecord(
            trip_id=row["trip_id"],
            hotel_id=row["hotel_id"],
            trip_name=row["trip_name"],
            check_in=date.fromisoformat(row["check_in"]),
            check_out=date.fromisoformat(row["check_out"]),
        )
        for row in trip_rows
    ]
    connected_hotels = connect_records_by_hotel_id(hotels, stays)
    return find_matching_hotels_by_name(hotel_name, connected_hotels)


def list_users(database_path: str | Path) -> list[UserRecord]:
    """Return every demo traveler in stable ID order."""

    with open_database(database_path) as connection:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()
    return [
        UserRecord(user_id=row["user_id"], display_name=row["display_name"])
        for row in rows
    ]


def list_booking_history(
    database_path: str | Path,
    user_id: str,
) -> list[BookingRecord]:
    """Return one traveler's confirmed and cancelled bookings."""

    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise InvalidBookingError("user_id must not be blank")

    with open_database(database_path) as connection:
        user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (normalized_user_id,),
        ).fetchone()
        if user_exists is None:
            raise RecordNotFoundError(
                f"User {normalized_user_id} was not found"
            )
        rows = connection.execute(
            f"""
            {BOOKING_SELECT_SQL}
            WHERE bookings.user_id = ?
            ORDER BY bookings.booked_on DESC, bookings.booking_id DESC
            """,
            (normalized_user_id,),
        ).fetchall()
    return [_booking_from_row(row) for row in rows]


def _require_related_record(
    connection: sqlite3.Connection,
    table: str,
    id_column: str,
    identifier: str,
    label: str,
) -> None:
    row = connection.execute(
        f"SELECT 1 FROM {table} WHERE {id_column} = ?",
        (identifier,),
    ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"{label} {identifier} was not found")


def _take_next_booking_id(connection: sqlite3.Connection) -> str:
    sequence_row = connection.execute(
        """
        SELECT next_value FROM id_sequences
        WHERE sequence_name = 'booking'
        """
    ).fetchone()
    if sequence_row is None:
        raise RuntimeError("Booking ID sequence is not initialized")

    next_value = sequence_row["next_value"]
    while True:
        booking_id = f"B{next_value:03d}"
        identifier_exists = connection.execute(
            "SELECT 1 FROM bookings WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()
        next_value += 1
        if identifier_exists is None:
            break

    connection.execute(
        """
        UPDATE id_sequences SET next_value = ?
        WHERE sequence_name = 'booking'
        """,
        (next_value,),
    )
    return booking_id


def create_booking(
    database_path: str | Path,
    user_id: str,
    trip_id: str,
    *,
    booked_on: date | None = None,
) -> BookingRecord:
    """Create a confirmed booking with a server-generated unique ID."""

    normalized_user_id = user_id.strip()
    normalized_trip_id = trip_id.strip()
    if not normalized_user_id:
        raise InvalidBookingError("user_id must not be blank")
    if not normalized_trip_id:
        raise InvalidBookingError("trip_id must not be blank")

    with open_database(database_path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            _require_related_record(
                connection, "users", "user_id", normalized_user_id, "User"
            )
            _require_related_record(
                connection, "trips", "trip_id", normalized_trip_id, "Trip"
            )
            booking_id = _take_next_booking_id(connection)
            connection.execute(
                """
                INSERT INTO bookings (
                    booking_id, user_id, trip_id, booked_on, status
                ) VALUES (?, ?, ?, ?, 'confirmed')
                """,
                (
                    booking_id,
                    normalized_user_id,
                    normalized_trip_id,
                    (booked_on or date.today()).isoformat(),
                ),
            )
            booking = _get_booking(connection, booking_id)
            connection.commit()
            return booking
        except Exception:
            connection.rollback()
            raise


def cancel_booking(
    database_path: str | Path,
    booking_id: str,
) -> BookingRecord:
    """Set a booking to cancelled; repeated cancellation is idempotent."""

    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise InvalidBookingError("booking_id must not be blank")

    with open_database(database_path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            booking = _get_booking(connection, normalized_booking_id)
            if booking.status != "cancelled":
                connection.execute(
                    """
                    UPDATE bookings SET status = 'cancelled'
                    WHERE booking_id = ?
                    """,
                    (normalized_booking_id,),
                )
                booking = _get_booking(connection, normalized_booking_id)
            connection.commit()
            return booking
        except Exception:
            connection.rollback()
            raise


def delete_booking(database_path: str | Path, booking_id: str) -> None:
    """Permanently remove one booking by its public ID."""

    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise InvalidBookingError("booking_id must not be blank")

    with open_database(database_path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "DELETE FROM bookings WHERE booking_id = ?",
                (normalized_booking_id,),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(
                    f"Booking {normalized_booking_id} was not found"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
