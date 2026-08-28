from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    chess_club = response.json()["Chess Club"]
    assert chess_club["description"]
    assert chess_club["schedule"]
    assert chess_club["max_participants"] == 12
    assert chess_club["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant():
    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Soccer Club"
    }
    assert "student@mergington.edu" in app_module.activities["Soccer Club"]["participants"]


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_full_activity():
    activity = app_module.activities["Art Club"]
    activity["participants"] = [
        f"student{number}@mergington.edu"
        for number in range(activity["max_participants"])
    ]

    response = client.post(
        "/activities/Art Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


@pytest.mark.parametrize("email", ["not-an-email", ""])
def test_signup_rejects_invalid_email(email):
    response = client.post("/activities/Soccer Club/signup", params={"email": email})

    assert response.status_code == 422


def test_signup_requires_email():
    response = client.post("/activities/Soccer Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_non_participant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


@pytest.mark.parametrize("email", ["not-an-email", ""])
def test_unregister_rejects_invalid_email(email):
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 422


def test_unregister_requires_email():
    response = client.delete("/activities/Chess Club/signup")

    assert response.status_code == 422