"""Load and search the Expedia Lite hotel and available-stay records."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class HotelRecord:
    """A hotel loaded from ``hotels.csv``."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal


@dataclass(frozen=True, slots=True)
class AvailableStayRecord:
    """An offered hotel stay loaded from ``trips.csv``."""

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


@dataclass(frozen=True, slots=True)
class HotelWithAvailableStays:
    """A hotel together with every offered stay that references it."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal
    available_stays: tuple[AvailableStayRecord, ...]


def _load_csv_rows(
    csv_path: str | Path,
    required_columns: set[str],
) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file and ensure its expected columns are present."""

    path = Path(csv_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing_columns = required_columns - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path} is missing required columns: {missing}")
        return [dict(row) for row in reader]


def load_hotel_records(csv_path: str | Path) -> list[HotelRecord]:
    """Load hotel records from ``hotels.csv``."""

    rows = _load_csv_rows(
        csv_path,
        {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
    )
    return [
        HotelRecord(
            hotel_id=row["hotel_id"],
            hotel_name=row["hotel_name"],
            city=row["city"],
            state=row["state"],
            nightly_rate_usd=Decimal(row["nightly_rate_usd"]),
        )
        for row in rows
    ]


def load_available_stay_records(csv_path: str | Path) -> list[AvailableStayRecord]:
    """Load offered stays from ``trips.csv``."""

    rows = _load_csv_rows(
        csv_path,
        {"trip_id", "hotel_id", "trip_name", "check_in", "check_out"},
    )
    return [
        AvailableStayRecord(
            trip_id=row["trip_id"],
            hotel_id=row["hotel_id"],
            trip_name=row["trip_name"],
            check_in=date.fromisoformat(row["check_in"]),
            check_out=date.fromisoformat(row["check_out"]),
        )
        for row in rows
    ]


def connect_records_by_hotel_id(
    hotels: Iterable[HotelRecord],
    available_stays: Iterable[AvailableStayRecord],
) -> list[HotelWithAvailableStays]:
    """Connect hotels and offered stays using their shared ``hotel_id``."""

    hotel_records = list(hotels)
    hotels_by_id = {hotel.hotel_id: hotel for hotel in hotel_records}
    if len(hotels_by_id) != len(hotel_records):
        raise ValueError("Hotel records contain a duplicate hotel_id")

    stays_by_hotel_id: dict[str, list[AvailableStayRecord]] = defaultdict(list)
    for stay in available_stays:
        if stay.hotel_id not in hotels_by_id:
            raise ValueError(
                f"Stay {stay.trip_id} references unknown hotel_id {stay.hotel_id}"
            )
        stays_by_hotel_id[stay.hotel_id].append(stay)

    return [
        HotelWithAvailableStays(
            hotel_id=hotel.hotel_id,
            hotel_name=hotel.hotel_name,
            city=hotel.city,
            state=hotel.state,
            nightly_rate_usd=hotel.nightly_rate_usd,
            available_stays=tuple(stays_by_hotel_id[hotel.hotel_id]),
        )
        for hotel in hotel_records
    ]


def find_matching_hotels_by_name(
    hotel_name: str,
    hotels: Iterable[HotelWithAvailableStays],
) -> list[HotelWithAvailableStays]:
    """Return hotels whose names contain the normalized search text."""

    normalized_name = hotel_name.strip().casefold()
    if not normalized_name:
        return []

    return [
        hotel
        for hotel in hotels
        if normalized_name in hotel.hotel_name.casefold()
    ]
