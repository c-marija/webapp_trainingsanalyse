"""Einzige Stelle, die das Sprachmodell aufruft (ADR 0001).

Der Aufruf ist eine gewöhnliche HTTP-Anfrage mit JSON an die REST-API von
Gemini, umgesetzt mit urllib aus der Standardbibliothek. Konfiguration über
Umgebungsvariablen (NFA-4):

    GEMINI_API_KEY   Pflicht
    GEMINI_MODEL     optional, Standard siehe DEFAULT_MODEL

Tests ersetzen generate() durch eine Attrappe und rufen die echte API nie auf.
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-2.5-flash"
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
# Gemessen am 2026-10-20: gemini-3.8-flash brauchte im kostenlosen Kontingent
# 97 Sekunden für eine Ein-Wort-Antwort. 30 Sekunden reichten nicht.
# Produktiv muss auch Gunicorn so lange warten (Option --timeout).
TIMEOUT_S = 150


class KiServiceError(Exception):
    """Das Sprachmodell hat keine Antwort geliefert. Die Meldung ist für die
    Anzeige in der Oberfläche gedacht (FA-E5)."""


def generate(prompt):
    """Schickt den Prompt an Gemini und gibt den Antworttext zurück."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise KiServiceError(
            "Die Trainingsempfehlungen sind noch nicht eingerichtet "
            "(kein API-Schlüssel hinterlegt)."
        )
    model = os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL

    request = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
        # Der Schlüssel gehört in den Header, nicht in die URL: URLs landen
        # leicht in Protokolldateien.
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise KiServiceError(
                "Das kostenlose Kontingent des Sprachmodells ist im Moment "
                "erschöpft. Bitte versuche es später nochmals."
            ) from error
        raise KiServiceError(
            f"Das Sprachmodell hat die Anfrage abgelehnt (HTTP {error.code})."
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise KiServiceError(
            "Das Sprachmodell ist nicht erreichbar. Bitte versuche es später nochmals."
        ) from error

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError):
        text = ""
    if not text:
        raise KiServiceError("Das Sprachmodell hat keine Antwort geliefert.")
    return text
