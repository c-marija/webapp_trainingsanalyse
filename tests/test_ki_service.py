"""Tests für ki_service.py. Die echte API wird nie aufgerufen: Der Client des
SDK bekommt eine Attrappe statt einer Netzwerkverbindung (MockTransport), die
festgelegte Antworten liefert. Der Code des SDK läuft dabei echt mit."""

import json

import anthropic
import httpx2
import pytest

from app import ki_service


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-schluessel")


def message(*blocks, stop_reason="end_turn"):
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": ki_service.MODEL,
        "content": list(blocks),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


def text(value):
    return {"type": "text", "text": value}


def fake_api(monkeypatch, status=200, body=None, exception=None):
    """Ersetzt make_client() durch einen Client mit Attrappe.

    Ohne Wiederholungen (max_retries=0), sonst warten die Tests bei Fehlern
    auf die Pausen des SDK.
    """
    requests = []

    def handler(request):
        requests.append(request)
        if exception:
            raise exception
        return httpx2.Response(status, json=body)

    def make_client():
        return anthropic.Anthropic(
            max_retries=0,
            http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
        )

    monkeypatch.setattr(ki_service, "make_client", make_client)
    return requests


def error_body(status):
    return {"type": "error", "error": {"type": "x", "message": f"Grund {status}"}}


def test_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ki_service.KiServiceError, match="kein API-Schlüssel"):
        ki_service.generate("Frage")


def test_returns_text_and_sends_model_and_key(monkeypatch, api_key):
    requests = fake_api(monkeypatch, body=message(text("Lauf "), text("locker.")))
    assert ki_service.generate("Frage") == "Lauf locker."

    request = requests[0]
    # Schlüssel im Header, nie in der URL (URLs landen in Protokollen).
    assert request.headers["authorization"] == "Bearer test-schluessel"
    assert "test-schluessel" not in str(request.url)
    sent = json.loads(request.content)
    assert sent["model"] == "claude-haiku-5-5"
    assert sent["output_config"] == {"effort": "medium"}
    assert sent["messages"] == [{"role": "user", "content": "Frage"}]


def test_skips_thinking_blocks(monkeypatch, api_key):
    """Haiku 5.5 kann mit Denk-Blöcken beginnen; nur der Text zählt."""
    thinking = {"type": "thinking", "thinking": "", "signature": "sig"}
    fake_api(monkeypatch, body=message(thinking, text("Antwort")))
    assert ki_service.generate("Frage") == "Antwort"


def test_client_stays_below_gunicorn_timeout():
    """Alle Versuche zusammen müssen vor Gunicorn (180 s) fertig sein."""
    client = ki_service.make_client()
    assert (client.max_retries + 1) * client.timeout < 180


@pytest.mark.parametrize(
    ("status", "message_pattern"),
    [
        (400, r"falsch eingerichtet.*\(HTTP 400\)"),
        (401, r"Schlüssel ist ungültig.*\(HTTP 401\)"),
        (402, r"Guthaben.*aufgebraucht.*\(HTTP 402\)"),
        (403, r"keine Berechtigung.*\(HTTP 403\)"),
        (404, r"Sprachmodell gibt es nicht.*\(HTTP 404\)"),
        (429, r"zu viele Anfragen.*\(HTTP 429\)"),
        (500, r"interner Fehler.*\(HTTP 500\)"),
        (503, r"interner Fehler.*\(HTTP 503\)"),
        (529, r"überlastet.*\(HTTP 529\)"),
        (418, r"abgelehnt.*\(HTTP 418\)"),
    ],
)
def test_http_errors_become_readable_messages(
    monkeypatch, api_key, status, message_pattern
):
    """FA-E5: Jede Störung wird zu einer Meldung, die sagt, was los ist."""
    fake_api(monkeypatch, status=status, body=error_body(status))
    with pytest.raises(ki_service.KiServiceError, match=message_pattern):
        ki_service.generate("Frage")


@pytest.mark.parametrize(
    ("exception", "message_pattern"),
    [
        (httpx2.ConnectError("offline"), "keine Verbindung"),
        (httpx2.ReadTimeout("zu langsam"), "nicht rechtzeitig"),
    ],
)
def test_network_errors_become_readable_messages(
    monkeypatch, api_key, exception, message_pattern
):
    fake_api(monkeypatch, exception=exception)
    with pytest.raises(ki_service.KiServiceError, match=message_pattern):
        ki_service.generate("Frage")


@pytest.mark.parametrize(
    "body",
    [
        message(),
        message(text("  ")),
        message(stop_reason="refusal"),
    ],
)
def test_no_usable_answer(monkeypatch, api_key, body):
    fake_api(monkeypatch, body=body)
    with pytest.raises(ki_service.KiServiceError, match="keine Antwort|abgelehnt"):
        ki_service.generate("Frage")


def test_http_error_is_logged_with_reason(monkeypatch, api_key, caplog):
    """Die Begründung von Anthropic steht im Protokoll, der Schlüssel nicht."""
    fake_api(monkeypatch, status=529, body=error_body(529))
    with pytest.raises(ki_service.KiServiceError):
        ki_service.generate("Frage")
    assert "HTTP 529" in caplog.text
    assert "Grund 529" in caplog.text
    assert ki_service.MODEL in caplog.text
    assert "test-schluessel" not in caplog.text
