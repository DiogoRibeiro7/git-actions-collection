import app


def test_get_message_default(monkeypatch):
    monkeypatch.delenv("APP_MESSAGE", raising=False)
    assert app.get_message() == "Hello from Docker"


def test_get_message_env(monkeypatch):
    monkeypatch.setenv("APP_MESSAGE", "From tests")
    assert app.get_message() == "From tests"
