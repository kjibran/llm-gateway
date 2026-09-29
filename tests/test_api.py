from fastapi.testclient import TestClient

from llm_gateway import main


def test_health_is_public():
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200


def test_chat_rejects_missing_key_when_configured(monkeypatch):
    monkeypatch.setattr(main.settings, "gateway_api_key", "secret")
    client = TestClient(main.app)
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 401
