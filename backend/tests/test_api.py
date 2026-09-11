from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_returns_matching_hotel_with_available_stays() -> None:
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


def test_search_returns_structured_empty_result_for_unknown_hotel() -> None:
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


def test_search_requires_hotel_name_query_parameter() -> None:
    response = client.get("/api/v1/hotels/search")

    assert response.status_code == 422
