"""SQLite connection, schema, and one-time starter-data initialization."""

from __future__ import annotations

import csv
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATABASE_PATH = DATA_DIRECTORY / "expedia_lite.sqlite3"
SEED_NAME = "starter-data-v1"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id TEXT PRIMARY KEY,
    hotel_name TEXT NOT NULL,
    city TEXT NOT NULL COLLATE NOCASE,
    state TEXT NOT NULL,
    nightly_rate_usd NUMERIC NOT NULL CHECK (nightly_rate_usd >= 0)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    trip_name TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    FOREIGN KEY (hotel_id) REFERENCES hotels (hotel_id) ON DELETE RESTRICT,
    CHECK (check_out > check_in)
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    booked_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT,
    FOREIGN KEY (trip_id) REFERENCES trips (trip_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS seed_state (
    seed_name TEXT PRIMARY KEY,
    applied_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS id_sequences (
    sequence_name TEXT PRIMARY KEY,
    next_value INTEGER NOT NULL CHECK (next_value > 0)
);

CREATE INDEX IF NOT EXISTS idx_trips_hotel_id ON trips (hotel_id);
CREATE INDEX IF NOT EXISTS idx_hotels_city ON hotels (city COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings (user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_trip_id ON bookings (trip_id);
"""


@contextmanager
def open_database(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a configured SQLite connection and close it after use."""

    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def _load_seed_rows(
    csv_path: Path,
    required_columns: set[str],
) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing_columns = required_columns - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{csv_path} is missing required columns: {missing}")
        return [dict(row) for row in reader]


def _ensure_unique_ids(
    rows: list[dict[str, str]],
    id_column: str,
    source_name: str,
) -> None:
    identifiers = [row[id_column] for row in rows]
    if any(not identifier for identifier in identifiers):
        raise ValueError(f"{source_name} contains a blank {id_column}")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{source_name} contains a duplicate {id_column}")


def _load_and_validate_seed_data(
    seed_directory: Path,
) -> dict[str, list[dict[str, str]]]:
    hotels = _load_seed_rows(
        seed_directory / "hotels.csv",
        {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
    )
    trips = _load_seed_rows(
        seed_directory / "trips.csv",
        {"trip_id", "hotel_id", "trip_name", "check_in", "check_out"},
    )
    users = _load_seed_rows(
        seed_directory / "users.csv",
        {"user_id", "display_name"},
    )
    bookings = _load_seed_rows(
        seed_directory / "bookings.csv",
        {"booking_id", "user_id", "trip_id", "booked_on", "status"},
    )

    for rows, id_column, source_name in (
        (hotels, "hotel_id", "hotels.csv"),
        (trips, "trip_id", "trips.csv"),
        (users, "user_id", "users.csv"),
        (bookings, "booking_id", "bookings.csv"),
    ):
        _ensure_unique_ids(rows, id_column, source_name)

    for hotel in hotels:
        try:
            rate = Decimal(hotel["nightly_rate_usd"])
        except InvalidOperation as error:
            raise ValueError(
                f"Hotel {hotel['hotel_id']} has an invalid nightly rate"
            ) from error
        if rate < 0:
            raise ValueError(f"Hotel {hotel['hotel_id']} has a negative nightly rate")

    hotel_ids = {hotel["hotel_id"] for hotel in hotels}
    for trip in trips:
        if trip["hotel_id"] not in hotel_ids:
            raise ValueError(
                f"Trip {trip['trip_id']} references unknown hotel_id "
                f"{trip['hotel_id']}"
            )
        check_in = date.fromisoformat(trip["check_in"])
        check_out = date.fromisoformat(trip["check_out"])
        if check_out <= check_in:
            raise ValueError(f"Trip {trip['trip_id']} must end after it begins")

    user_ids = {user["user_id"] for user in users}
    trip_ids = {trip["trip_id"] for trip in trips}
    for booking in bookings:
        if booking["user_id"] not in user_ids:
            raise ValueError(
                f"Booking {booking['booking_id']} references unknown user_id "
                f"{booking['user_id']}"
            )
        if booking["trip_id"] not in trip_ids:
            raise ValueError(
                f"Booking {booking['booking_id']} references unknown trip_id "
                f"{booking['trip_id']}"
            )
        date.fromisoformat(booking["booked_on"])
        if booking["status"] not in {"confirmed", "cancelled"}:
            raise ValueError(
                f"Booking {booking['booking_id']} has an invalid status"
            )

    return {
        "hotels": hotels,
        "trips": trips,
        "users": users,
        "bookings": bookings,
    }


def _next_booking_number(bookings: list[dict[str, str]]) -> int:
    numbers: list[int] = []
    for booking in bookings:
        booking_id = booking["booking_id"]
        if not booking_id.startswith("B") or not booking_id[1:].isdigit():
            raise ValueError(f"Unsupported starter booking_id: {booking_id}")
        numbers.append(int(booking_id[1:]))
    return max(numbers, default=0) + 1


def _data_tables_are_empty(connection: sqlite3.Connection) -> bool:
    return all(
        connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        for table in ("hotels", "trips", "users", "bookings")
    )


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    seed_directory: str | Path = DATA_DIRECTORY,
) -> None:
    """Create the schema and atomically import starter CSVs exactly once."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open_database(path) as connection:
        connection.executescript(SCHEMA_SQL)

        seed_exists = connection.execute(
            "SELECT 1 FROM seed_state WHERE seed_name = ?",
            (SEED_NAME,),
        ).fetchone()
        if seed_exists:
            return

        seed_data = _load_and_validate_seed_data(Path(seed_directory))

        try:
            connection.execute("BEGIN IMMEDIATE")
            seed_exists = connection.execute(
                "SELECT 1 FROM seed_state WHERE seed_name = ?",
                (SEED_NAME,),
            ).fetchone()
            if seed_exists:
                connection.commit()
                return

            if not _data_tables_are_empty(connection):
                raise RuntimeError(
                    "Database contains application data without a seed marker; "
                    "refusing to overwrite or merge it"
                )

            connection.executemany(
                """
                INSERT INTO hotels (
                    hotel_id, hotel_name, city, state, nightly_rate_usd
                ) VALUES (
                    :hotel_id, :hotel_name, :city, :state, :nightly_rate_usd
                )
                """,
                seed_data["hotels"],
            )
            connection.executemany(
                """
                INSERT INTO trips (
                    trip_id, hotel_id, trip_name, check_in, check_out
                ) VALUES (
                    :trip_id, :hotel_id, :trip_name, :check_in, :check_out
                )
                """,
                seed_data["trips"],
            )
            connection.executemany(
                """
                INSERT INTO users (user_id, display_name)
                VALUES (:user_id, :display_name)
                """,
                seed_data["users"],
            )
            connection.executemany(
                """
                INSERT INTO bookings (
                    booking_id, user_id, trip_id, booked_on, status
                ) VALUES (
                    :booking_id, :user_id, :trip_id, :booked_on, :status
                )
                """,
                seed_data["bookings"],
            )
            connection.execute(
                """
                INSERT INTO id_sequences (sequence_name, next_value)
                VALUES ('booking', ?)
                """,
                (_next_booking_number(seed_data["bookings"]),),
            )
            connection.execute(
                """
                INSERT INTO seed_state (seed_name, applied_on)
                VALUES (?, ?)
                """,
                (SEED_NAME, date.today().isoformat()),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
