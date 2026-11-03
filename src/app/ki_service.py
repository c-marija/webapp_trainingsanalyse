"""Einzige Stelle, die das Sprachmodell aufruft (ADR 0004).

Der Aufruf geht über das offizielle Python-SDK von Anthropic an Claude.
Konfiguration über die Umgebung (NFA-4):

    ANTHROPIC_API_KEY   Pflicht, erhältlich in der Claude Console

Tests ersetzen make_client() bzw. generate() durch eine Attrappe und rufen
die echte API nie auf.
"""

import logging
import os

import anthropic

# ADR 0004: Claude Haiku 5.5 — schnell und günstig, reicht für eine kurze
# Trainingsempfehlung. Wechsel des Modells: nur diese Zeile ändern.
MODEL = "claude-haiku-5-5"
# Haiku 5.5 denkt vor der Antwort nach (adaptive thinking). "medium" ist die
# Voreinstellung des Modells, hier ausdrücklich gesetzt.
EFFORT = "medium"
# Obergrenze für Nachdenken und Antwort zusammen.
MAX_TOKENS = 16000
# Das SDK wiederholt bei Überlastung (429, 5xx) und Verbindungsfehlern
# selbstständig, bis zu MAX_RETRIES-mal. Im ungünstigsten Fall dauert ein
# Aufruf also (MAX_RETRIES + 1) × TIMEOUT_S plus kurze Pausen — das muss unter
# dem Gunicorn-Timeout von 180 Sekunden bleiben (Dockerfile).
TIMEOUT_S = 50
MAX_RETRIES = 2

logger = logging.getLogger(__name__)

# FA-E5: verständliche Meldung je Fehlercode. Bei 4xx liegt der Fehler bei
# unserer Einrichtung, ein neuer Versuch hilft nicht. Bei 429 und 5xx liegt er
# bei Anthropic, später nochmals versuchen kann helfen.
HTTP_MESSAGES = {
    400: "Die Trainingsempfehlungen sind falsch eingerichtet: Die Anfrage an "
    "das Sprachmodell war ungültig.",
    401: "Die Trainingsempfehlungen sind falsch eingerichtet: Der API-Schlüssel "
    "ist ungültig.",
    402: "Das Guthaben für das Sprachmodell ist aufgebraucht. Bitte das "
    "Projektteam informieren.",
    403: "Die Trainingsempfehlungen sind falsch eingerichtet: Der API-Schlüssel "
    "hat keine Berechtigung für dieses Sprachmodell.",
    404: "Die Trainingsempfehlungen sind falsch eingerichtet: Das eingestellte "
    "Sprachmodell gibt es nicht.",
    429: "Das Sprachmodell erhält im Moment zu viele Anfragen. Bitte versuche "
    "es in einer Minute nochmals.",
    500: "Beim Sprachmodell ist ein interner Fehler aufgetreten. Bitte versuche "
    "es nochmals.",
    529: "Das Sprachmodell ist im Moment überlastet. Bitte versuche es in ein "
    "paar Minuten nochmals.",
}


class KiServiceError(Exception):
    """Das Sprachmodell hat keine Antwort geliefert. Die Meldung ist für die
    Anzeige in der Oberfläche gedacht (FA-E5)."""


def make_client():
    return anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=MAX_RETRIES)


def generate(prompt):
    """Schickt den Prompt an Claude und gibt den Antworttext zurück."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise KiServiceError(
            "Die Trainingsempfehlungen sind noch nicht eingerichtet "
            "(kein API-Schlüssel hinterlegt)."
        )

    try:
        response = make_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            output_config={"effort": EFFORT},
            messages=[{"role": "user", "content": prompt}],
        )
    # Reihenfolge wichtig: APITimeoutError ist ein Sonderfall von
    # APIConnectionError und muss darum zuerst geprüft werden.
    except anthropic.APITimeoutError as error:
        logger.warning("Claude: Zeitüberschreitung (Modell %s)", MODEL)
        raise KiServiceError(
            "Das Sprachmodell hat nicht rechtzeitig geantwortet. Bitte versuche "
            "es nochmals."
        ) from error
    except anthropic.APIConnectionError as error:
        logger.warning("Claude nicht erreichbar (Modell %s): %r", MODEL, error)
        raise KiServiceError(
            "Das Sprachmodell ist nicht erreichbar (keine Verbindung zu "
            "Anthropic). Bitte versuche es später nochmals."
        ) from error
    except anthropic.APIStatusError as error:
        # Begründung von Anthropic ins Protokoll (bei Render unter "Logs"),
        # damit das Team die Ursache sieht. Den Benutzern zeigen wir eine
        # Meldung, die sagt, was los ist und ob sich ein neuer Versuch lohnt.
        logger.warning(
            "Claude HTTP %s (Modell %s): %s", error.status_code, MODEL, error.message
        )
        message = HTTP_MESSAGES.get(error.status_code)
        if message is None and error.status_code >= 500:
            message = HTTP_MESSAGES[500]
        if message is None:
            message = "Das Sprachmodell hat die Anfrage abgelehnt."
        raise KiServiceError(f"{message} (HTTP {error.status_code})") from error

    # Sicherheitsfilter: Das Modell kann eine Anfrage ablehnen. Das kommt als
    # normale Antwort mit stop_reason "refusal", nicht als Fehler.
    if response.stop_reason == "refusal":
        logger.warning("Claude hat abgelehnt: %s", response.stop_details)
        raise KiServiceError(
            "Das Sprachmodell hat diese Anfrage abgelehnt. Bitte formuliere die "
            "Einschränkungen in den Rückfragen anders."
        )

    # Die Antwort kann mit Denk-Blöcken ("thinking") beginnen. Darum nach Typ
    # filtern statt einfach den ersten Block zu nehmen.
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise KiServiceError("Das Sprachmodell hat keine Antwort geliefert.")
    return text
