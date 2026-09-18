from fastapi.testclient import TestClient

def test_search_returns_matching_hotel_with_available_stays(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/hotels/search",
        params={"hotel_name": "harbor lantern"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "harbor lantern",
        "count": 1,
        "hotels": [
            {
                "hotel_id": "H001",
                "hotel_name": "Harbor Lantern Hotel",
                "city": "Boston",
                "state": "MA",
                "nightly_rate_usd": 150.0,
                "available_stays": [
                    {
                        "trip_id": "T001",
                        "hotel_id": "H001",
                        "trip_name": "Boston Harbor Weekend",
                        "check_in": "2026-09-18",
                        "check_out": "2026-09-20",
                    },
                    {
                        "trip_id": "T009",
                        "hotel_id": "H001",
                        "trip_name": "Boston Autumn Weekend",
                        "check_in": "2026-10-02",
                        "check_out": "2026-10-04",
                    },
                ],
            }
        ],
    }


def test_search_returns_structured_empty_result_for_unknown_hotel(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/hotels/search",
        params={"hotel_name": "Ocean Palace"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "Ocean Palace",
        "count": 0,
        "hotels": [],
    }


def test_search_requires_hotel_name_query_parameter(client: TestClient) -> None:
    response = client.get("/api/v1/hotels/search")

    assert response.status_code == 422


def test_lists_demo_users_and_booking_history(client: TestClient) -> None:
    users_response = client.get("/api/v1/users")
    history_response = client.get("/api/v1/users/U001/bookings")
    empty_history_response = client.get("/api/v1/users/U006/bookings")

    assert users_response.status_code == 200
    assert users_response.json()["count"] == 6
    assert users_response.json()["users"][0] == {
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
    }
    assert history_response.status_code == 200
    assert history_response.json()["count"] == 2
    assert {
        booking["booking_id"]: booking["status"]
        for booking in history_response.json()["bookings"]
    } == {"B001": "confirmed", "B002": "cancelled"}
    assert empty_history_response.json() == {
        "user_id": "U006",
        "count": 0,
        "bookings": [],
    }


def test_create_cancel_and_delete_a_new_test_booking(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={"user_id": "U006", "trip_id": "T001"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["booking_id"] == "B007"
    assert created["status"] == "confirmed"
    assert created["user_id"] == "U006"
    assert created["trip_id"] == "T001"
    assert created["nights"] == 2
    assert created["nightly_rate_usd"] == 150.0
    assert created["stay_price_usd"] == 300.0

    first_cancel_response = client.patch(
        "/api/v1/bookings/B007",
        json={"status": "cancelled"},
    )
    second_cancel_response = client.patch(
        "/api/v1/bookings/B007",
        json={"status": "cancelled"},
    )

    assert first_cancel_response.status_code == 200
    assert second_cancel_response.status_code == 200
    assert first_cancel_response.json() == second_cancel_response.json()
    assert second_cancel_response.json()["status"] == "cancelled"

    delete_response = client.delete("/api/v1/bookings/B007")
    history_response = client.get("/api/v1/users/U006/bookings")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert history_response.json()["bookings"] == []


def test_duplicate_active_bookings_are_allowed(client: TestClient) -> None:
    first = client.post(
        "/api/v1/bookings",
        json={"user_id": "U006", "trip_id": "T001"},
    )
    second = client.post(
        "/api/v1/bookings",
        json={"user_id": "U006", "trip_id": "T001"},
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["booking_id"] == "B007"
    assert second.json()["booking_id"] == "B008"


def test_booking_routes_report_invalid_or_unknown_input(client: TestClient) -> None:
    unknown_user = client.get("/api/v1/users/U999/bookings")
    blank_user = client.post(
        "/api/v1/bookings",
        json={"user_id": "   ", "trip_id": "T001"},
    )
    unknown_trip = client.post(
        "/api/v1/bookings",
        json={"user_id": "U001", "trip_id": "T999"},
    )
    invalid_status = client.patch(
        "/api/v1/bookings/B001",
        json={"status": "confirmed"},
    )
    unknown_delete = client.delete("/api/v1/bookings/B999")

    assert unknown_user.status_code == 404
    assert blank_user.status_code == 422
    assert unknown_trip.status_code == 404
    assert invalid_status.status_code == 422
    assert unknown_delete.status_code == 404
