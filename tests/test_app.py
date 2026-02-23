"""
Tests for Mergington High School Activities API
Using Arrange-Act-Assert (AAA) pattern for test structure
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }
    activities.clear()
    activities.update(initial_state)
    yield
    activities.clear()
    activities.update(initial_state)


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        # Arrange: No setup needed

        # Act: Make request to root
        response = client.get("/", follow_redirects=False)

        # Assert: Should redirect to static/index.html
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client, reset_activities):
        # Arrange: Activities already initialized by fixture

        # Act: Fetch all activities
        response = client.get("/activities")

        # Assert: Should return 200 with activities dict
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_structure(self, client, reset_activities):
        # Arrange: Activities initialized

        # Act: Get activities
        response = client.get("/activities")

        # Assert: Each activity has required fields
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_participants_list(self, client, reset_activities):
        # Arrange: Activities initialized

        # Act: Get activities
        response = client.get("/activities")

        # Assert: Verify participant data
        data = response.json()
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
        assert len(data["Programming Class"]["participants"]) == 2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client, reset_activities):
        # Arrange: New email not yet registered
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act: Sign up for activity
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert: Should succeed and add participant
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_duplicate_participant(self, client, reset_activities):
        # Arrange: Email already signed up for activity
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered

        # Act: Try to sign up again
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert: Should return 400 error
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity(self, client, reset_activities):
        # Arrange: Activity doesn't exist
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # Act: Try to sign up for nonexistent activity
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert: Should return 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_multiple_activities(self, client, reset_activities):
        # Arrange: Student will sign up for multiple activities
        email = "versatile@mergington.edu"

        # Act: Sign up for two different activities
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )

        # Assert: Both signups should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_participant(self, client, reset_activities):
        # Arrange: Participant is registered
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act: Unregister from activity
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert: Should succeed and remove participant
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_nonexistent_participant(self, client, reset_activities):
        # Arrange: Email is not signed up
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act: Try to unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert: Should return 400 error
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        # Arrange: Activity doesn't exist
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # Act: Try to unregister from nonexistent activity
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert: Should return 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_all_participants(self, client, reset_activities):
        # Arrange: Activity has multiple participants
        activity_name = "Chess Club"
        participants = activities[activity_name]["participants"].copy()

        # Act: Unregister each participant
        for email in participants:
            response = client.delete(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert: Activity should have no participants
        assert len(activities[activity_name]["participants"]) == 0
