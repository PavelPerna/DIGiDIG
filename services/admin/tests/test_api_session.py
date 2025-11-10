from fastapi.testclient import TestClient
import sys
import os

# Ensure the service src directory is on sys.path so tests can import the FastAPI app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# Also add the repository root so `lib` package imports succeed (repo root is three levels up)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import app as admin_app

client = TestClient(admin_app.app)


def test_api_session_unauthenticated():
    """Without monkeypatching, the endpoint should return 401 when not authenticated."""
    resp = client.get("/api/session")
    assert resp.status_code == 401


def test_api_session_authenticated(monkeypatch):
    """When get_user_from_token returns a user dict, /api/session should return 200 and the user json."""
    async def fake_get_user_from_token(request):
        return {"status": "OK", "username": "admin", "roles": ["admin"]}

    monkeypatch.setattr(admin_app, "get_user_from_token", fake_get_user_from_token)

    resp = client.get("/api/session")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("username") == "admin"
    assert "roles" in body
