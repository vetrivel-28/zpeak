from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Meeting Knowledge Assistant"}

def test_explain_text():
    response = client.post("/explain", json={"text": "The Kubernetes deployment failed."})
    assert response.status_code == 200
    data = response.json()
    assert "known_terms" in data
    assert "new_terms" in data
    assert "unknown_terms" in data

def test_explain_term():
    response = client.post("/term", json={"term": "LangGraph"})
    assert response.status_code == 200
    data = response.json()
    assert "term" in data
    assert "definition" in data
    assert "category" in data
    assert "source" in data

def test_search():
    response = client.get("/search?q=kubernetes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_terms" in data
    assert "categories" in data
    assert "ai_generated" in data
