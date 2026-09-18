from pathlib import Path

import pytest

from app.database import SEED_NAME, initialize_database, open_database


def test_initializes_schema_and_all_starter_records(database_path: Path) -> None:
    with open_database(database_path) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        }
        seed = connection.execute(
            "SELECT seed_name FROM seed_state WHERE seed_name = ?",
            (SEED_NAME,),
        ).fetchone()
        next_booking_number = connection.execute(
            """
            SELECT next_value FROM id_sequences
            WHERE sequence_name = 'booking'
            """
        ).fetchone()[0]
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert counts == {"hotels": 8, "trips": 12, "users": 6, "bookings": 6}
    assert seed["seed_name"] == SEED_NAME
    assert next_booking_number == 7
    assert foreign_key_errors == []


def test_later_initialization_preserves_updates_and_deletions(
    database_path: Path,
) -> None:
    with open_database(database_path) as connection:
        connection.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = 'B001'"
        )
        connection.execute("DELETE FROM bookings WHERE booking_id = 'B006'")
        connection.commit()

    initialize_database(database_path)

    with open_database(database_path) as connection:
        b001_status = connection.execute(
            "SELECT status FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()["status"]
        b006 = connection.execute(
            "SELECT booking_id FROM bookings WHERE booking_id = 'B006'"
        ).fetchone()
        booking_count = connection.execute(
            "SELECT COUNT(*) FROM bookings"
        ).fetchone()[0]

    assert b001_status == "cancelled"
    assert b006 is None
    assert booking_count == 5


def test_refuses_to_merge_nonempty_data_without_a_seed_marker(
    database_path: Path,
) -> None:
    with open_database(database_path) as connection:
        connection.execute("DELETE FROM seed_state WHERE seed_name = ?", (SEED_NAME,))
        connection.commit()

    with pytest.raises(RuntimeError, match="refusing to overwrite or merge"):
        initialize_database(database_path)

    with open_database(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 6
