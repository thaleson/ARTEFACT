from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.application.contracts import AgentResponse
from app.presentation.api import create_app


def test_health_and_chat_routes() -> None:
    agent = Mock()
    agent.respond.return_value = AgentResponse(
        reply="Olá!",
        mode="offline",
    )
    client = TestClient(create_app(agent))

    health = client.get("/health")
    chat = client.post("/chat", json={"message": "Olá"})

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert chat.status_code == 200
    assert chat.json()["reply"] == "Olá!"


def test_chat_route_rejects_blank_message() -> None:
    client = TestClient(create_app(Mock()))

    response = client.post("/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_controller_maps_service_errors() -> None:
    cases = (
        (ValueError("bad input"), 400),
        (RuntimeError("temporary"), 503),
        (Exception("unexpected"), 500),
    )
    for error, status_code in cases:
        agent = Mock()
        agent.respond.side_effect = error
        client = TestClient(create_app(agent))

        response = client.post("/chat", json={"message": "hello"})

        assert response.status_code == status_code
