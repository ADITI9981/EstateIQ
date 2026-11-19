
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200


def test_chat_endpoint():
    response = client.post(
        "/chat",
        json={"question": "What is the rent for two payments?"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "What is the rent for two payments?"
    assert "125,000" in data["answer"]
    assert len(data["sources"]) > 0


def test_chat_rejects_empty_question():
    response = client.post(
        "/chat",
        json={"question": ""}
    )

    assert response.status_code == 422
