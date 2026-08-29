import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_daily_synthesis_route():
    response = client.get("/api/synthesis/daily")
    assert response.status_code == 200
    data = response.json()
    assert "density" in data
    assert "score" in data["density"]
    assert "today_events" in data
    assert "coaching_nudge" in data

def test_voice_thought_processing_idea():
    payload = {
        "user_id": "default-user",
        "transcript": "I want to build an AI agent for real estate market analysis."
    }
    response = client.post("/api/voice/process-thought", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "BIG_IDEA"
    assert data["idea_analysis"] is not None

def test_calendar_density_route():
    response = client.get("/api/calendar/density?days=7")
    assert response.status_code == 200
    data = response.json()
    assert len(data["snapshots"]) == 7

def test_nlp_command_route():
    payload = {
        "user_id": "default-user",
        "command": "Clear my Friday morning"
    }
    response = client.post("/api/nlp/command", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["mutations"]) >= 1
