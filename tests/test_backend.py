import os
import sys
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add parent backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from config import settings

client = TestClient(app)

# 1. Test Session Creation in Development Auth Mode
def test_session_creation_dev_mode():
    settings.AUTH_MODE = "development"
    response = client.post("/session/start")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["learner_id"] == "dev-user"
    assert data["selected_career"] is None
    assert data["learning_path"] == []

# 2. Test Session Persistence for Same Authenticated User
def test_session_persistence_for_same_user():
    settings.AUTH_MODE = "development"
    res1 = client.post("/session/start")
    sess1 = res1.json()

    # Second call for same dev user returns existing session
    res2 = client.post("/session/start")
    sess2 = res2.json()
    assert sess1["session_id"] == sess2["session_id"]

# 3. Test Missing Authentication in Firebase Mode
def test_missing_auth_firebase_mode():
    settings.AUTH_MODE = "firebase"
    response = client.post("/session/start")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["detail"]

# 4. Test Invalid Token in Firebase Mode
def test_invalid_token_firebase_mode():
    settings.AUTH_MODE = "firebase"
    with patch("auth.dependencies.verify_firebase_token", side_effect=ValueError("Token expired")):
        headers = {"Authorization": "Bearer invalid_token_123"}
        response = client.post("/session/start", headers=headers)
        assert response.status_code == 401
        assert "Invalid or expired Firebase ID token" in response.json()["detail"]

# 5. Test Valid Token Verification in Firebase Mode
def test_valid_firebase_token():
    settings.AUTH_MODE = "firebase"
    mock_decoded = {"uid": "firebase-uid-999", "email": "firebase@example.com", "name": "Firebase User"}
    with patch("auth.dependencies.verify_firebase_token", return_value=mock_decoded):
        headers = {"Authorization": "Bearer valid_firebase_token_abc"}
        response = client.post("/session/start", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["learner_id"] == "firebase-uid-999"

# 6. Test Session Ownership Enforcement (403 Forbidden on Cross-User Access)
def test_session_ownership_forbidden():
    settings.AUTH_MODE = "firebase"
    user_a_decoded = {"uid": "user-a-123", "email": "a@example.com"}
    user_b_decoded = {"uid": "user-b-456", "email": "b@example.com"}

    # User A creates session
    with patch("auth.dependencies.verify_firebase_token", return_value=user_a_decoded):
        res = client.post("/session/start", headers={"Authorization": "Bearer token_a"})
        session_id = res.json()["session_id"]

    # User B attempts to select career on User A's session -> 403 Forbidden
    with patch("auth.dependencies.verify_firebase_token", return_value=user_b_decoded):
        res_forbidden = client.post(
            f"/session/{session_id}/career",
            headers={"Authorization": "Bearer token_b"},
            json={"career_id": "data-analyst"}
        )
        assert res_forbidden.status_code == 403
        assert "Forbidden" in res_forbidden.json()["detail"]

# 7. Test Career Listing (Public endpoint)
def test_career_listing():
    settings.AUTH_MODE = "firebase"
    # No auth header needed for public career listing
    response = client.get("/careers")
    assert response.status_code == 200
    careers = response.json()
    assert len(careers) >= 15

# 8. Test Full End-to-End Flow in Development Mode
def test_e2e_flow_dev_mode():
    settings.AUTH_MODE = "development"
    # Start session
    session_id = client.post("/session/start").json()["session_id"]

    # Select career
    sel_res = client.post(f"/session/{session_id}/career", json={"career_id": "data-analyst"})
    assert sel_res.status_code == 200

    # Start assessment
    start_data = client.post(f"/assessment/start?session_id={session_id}").json()
    assessment_id = start_data["assessment_id"]

    # Submit assessment
    answers = [{"question_id": q["id"], "answer": q["options"][0]} for q in start_data["questions"]]
    sub_res = client.post(
        f"/assessment/{assessment_id}/submit?session_id={session_id}",
        json={"assessment_id": assessment_id, "answers": answers}
    )
    assert sub_res.status_code == 200

    # Get skill gaps
    skills_res = client.get(f"/session/{session_id}/skills")
    assert skills_res.status_code == 200

    # Get path
    path_res = client.get(f"/session/{session_id}/path")
    assert path_res.status_code == 200
    assert len(path_res.json()["learning_path"]) > 0

    # Chat
    chat_res = client.post("/chat", json={"session_id": session_id, "message": "What should I focus on next?"})
    assert chat_res.status_code == 200
    assert "response" in chat_res.json()

    # Feedback
    fb_res = client.post(
        f"/session/{session_id}/feedback",
        json={"milestone_order": 1, "rating": 5, "feedback_text": "Awesome road!"}
    )
    assert fb_res.status_code == 200

    # Trace
    trace_res = client.get(f"/session/{session_id}/trace")
    assert trace_res.status_code == 200
    assert len(trace_res.json()) > 0
