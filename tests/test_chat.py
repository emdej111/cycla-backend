def test_chat_send_message_appends_disclaimer(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.chat.get_chat_response",
        lambda message, conversation_history, context: "Here's what I'd suggest for today.",
    )
    response = client.post("/chat/", json={"message": "Why am I so tired?"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Here's what I'd suggest for today."
    assert body["disclaimer"] == "This is not medical advice. Consult your healthcare provider."


def test_chat_history_records_both_user_and_assistant_messages(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.chat.get_chat_response",
        lambda message, conversation_history, context: "Got it.",
    )
    client.post("/chat/", json={"message": "Hello Cycla"}, headers=auth_headers)

    history = client.get("/chat/history", headers=auth_headers)
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello Cycla"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Got it."


def test_chat_falls_back_gracefully_when_claude_errors(client, auth_headers, monkeypatch):
    def _boom(message, conversation_history, context):
        raise RuntimeError("network error")

    monkeypatch.setattr("src.api.routes.chat.get_chat_response", _boom)
    response = client.post("/chat/", json={"message": "hi"}, headers=auth_headers)
    assert response.status_code == 200
    assert "trouble connecting" in response.json()["reply"]


def test_chat_requires_authentication(client):
    response = client.post("/chat/", json={"message": "hi"})
    assert response.status_code == 401
