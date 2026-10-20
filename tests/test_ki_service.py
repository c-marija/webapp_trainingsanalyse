"""Tests für ki_service.py. Die echte API wird nie aufgerufen: urlopen wird
durch eine Attrappe ersetzt, die festgelegte Antworten liefert."""

import io
import json
import urllib.error

import pytest

from app import ki_service


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-schluessel")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)


def fake_urlopen(monkeypatch, result):
    calls = []

    def urlopen(request, timeout):
        calls.append(request)
        if isinstance(result, Exception):
            raise result
        return FakeResponse(json.dumps(result).encode())

    monkeypatch.setattr(ki_service.urllib.request, "urlopen", urlopen)
    return calls


def test_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ki_service.KiServiceError, match="kein API-Schlüssel"):
        ki_service.generate("Frage")


def test_returns_text_and_sends_key_in_header(monkeypatch, api_key):
    calls = fake_urlopen(
        monkeypatch,
        {
            "candidates": [
                {"content": {"parts": [{"text": "Lauf "}, {"text": "locker."}]}}
            ]
        },
    )
    assert ki_service.generate("Frage") == "Lauf locker."

    request = calls[0]
    assert request.get_header("X-goog-api-key") == "test-schluessel"
    assert "test-schluessel" not in request.full_url
    assert ki_service.DEFAULT_MODEL in request.full_url
    assert json.loads(request.data)["contents"][0]["parts"][0]["text"] == "Frage"


def test_model_from_environment(monkeypatch, api_key):
    monkeypatch.setenv("GEMINI_MODEL", "anderes-modell")
    calls = fake_urlopen(
        monkeypatch, {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    )
    ki_service.generate("Frage")
    assert "/models/anderes-modell:" in calls[0].full_url


@pytest.mark.parametrize(
    ("result", "message"),
    [
        (urllib.error.HTTPError("url", 429, "Too Many", {}, None), "Kontingent"),
        (urllib.error.HTTPError("url", 403, "Forbidden", {}, None), "HTTP 403"),
        (urllib.error.URLError("offline"), "nicht erreichbar"),
        (TimeoutError(), "nicht erreichbar"),
        ({"candidates": []}, "keine Antwort"),
        ({"candidates": [{"content": {"parts": [{"text": "  "}]}}]}, "keine Antwort"),
    ],
)
def test_errors_become_readable_messages(monkeypatch, api_key, result, message):
    """FA-E5: Jede Störung wird zu einer verständlichen Meldung."""
    fake_urlopen(monkeypatch, result)
    with pytest.raises(ki_service.KiServiceError, match=message):
        ki_service.generate("Frage")
