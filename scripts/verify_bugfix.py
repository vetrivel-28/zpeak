from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

tests = [
    "LangGraph",
    "CrewAI",
    "OpenTelemetry",
    "HyperVectorAgentMeshX9000",
    "QuantumMeshAgent2029",
    "The LangGraph workflow sends traces to OpenTelemetry.",
    "Hey guys I fixed the bug yesterday."
]

for t in tests:
    print(f"\nTesting: {t}")
    response = client.post("/term", json={"term": t})
    if response.status_code == 400:
        print(f"HTTP 400: {response.json()}")
    else:
        data = response.json()
        print(f"Result: {data}")
