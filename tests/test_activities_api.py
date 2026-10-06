from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Coding Club"
EXISTING_EMAIL = "student@mergington.edu"


@pytest.fixture
def client(monkeypatch):
    activities = {
        ACTIVITY_NAME: {
            "description": "Learn to code",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 2,
            "participants": [EXISTING_EMAIL],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def activity_url():
    return f"/activities/{quote(ACTIVITY_NAME, safe='')}/signup"


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = {
        ACTIVITY_NAME: {
            "description": "Learn to code",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 2,
            "participants": [EXISTING_EMAIL],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    new_email = "new-student@mergington.edu"

    # Act
    response = client.post(activity_url(), params={"email": new_email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {new_email} for {ACTIVITY_NAME}"
    }
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == [
        EXISTING_EMAIL,
        new_email,
    ]


def test_signup_rejects_duplicate_participant_without_changing_state(client):
    # Arrange
    original_participants = [EXISTING_EMAIL]

    # Act
    response = client.post(activity_url(), params={"email": EXISTING_EMAIL})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_url = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.post(unknown_url, params={"email": "new-student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]


def test_unregister_removes_participant(client):
    # Arrange
    email_to_remove = EXISTING_EMAIL

    # Act
    response = client.delete(activity_url(), params={"email": email_to_remove})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email_to_remove} from {ACTIVITY_NAME}"
    }
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == []


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    unknown_url = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.delete(unknown_url, params={"email": EXISTING_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]


def test_unregister_rejects_unregistered_participant_without_changing_state(client):
    # Arrange
    unknown_email = "not-signed-up@mergington.edu"

    # Act
    response = client.delete(activity_url(), params={"email": unknown_email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == [EXISTING_EMAIL]