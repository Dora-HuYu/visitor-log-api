import pytest
from fastapi.testclient import TestClient

from main import app, visitors
from plates import is_valid_singapore_plate


@pytest.fixture
def client():
    # Start each API test with an empty visitor log.
    visitors.clear()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        visitors.clear()


def test_vehicle_cannot_check_in_twice_before_checkout(client):
    payload = {
        "name": "Jamie Tan",
        "unit_number": "#08-12",
        "vehicle_plate": "SBA1234G",
    }

    first = client.post("/visitors", json=payload)
    assert first.status_code == 201
    visit_id = first.json()["id"]

    # The same plate with different spacing and case is still a duplicate.
    duplicate_payload = {**payload, "vehicle_plate": "sba 1234 g"}
    duplicate = client.post("/visitors", json=duplicate_payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Vehicle is already checked in"

    checkout = client.post(f"/visitors/{visit_id}/checkout")
    assert checkout.status_code == 200

    # Once the first visit ends, the vehicle can start a new visit.
    next_visit = client.post("/visitors", json=payload)
    assert next_visit.status_code == 201
    assert next_visit.json()["id"] != visit_id


@pytest.mark.parametrize(
    ("plate", "expected"),
    [
        ("SBA1234G", True),
        ("SBA1234A", False),
        ("E23H", True),
        ("SBA12345G", False),
        ("SBA1234", False),
    ],
)
def test_singapore_plate_validation(plate, expected):
    assert is_valid_singapore_plate(plate) is expected


def test_registration_rejects_invalid_check_letter(client):
    response = client.post(
        "/visitors",
        json={
            "name": "Jamie Tan",
            "unit_number": "#08-12",
            "vehicle_plate": "SBA1234A",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid Singapore vehicle plate"
    assert not visitors