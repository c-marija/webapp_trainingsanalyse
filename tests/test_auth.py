"""Tests für /api/auth (FA-A1 bis FA-A4)."""

import pytest

from app.seed import DEMO_USERS

DEMO = DEMO_USERS[0]


def login(client, email=DEMO["email"], password=DEMO["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_returns_user(client):
    response = login(client)
    assert response.status_code == 200
    assert response.get_json() == {"name": DEMO["name"], "email": DEMO["email"]}


def test_login_normalizes_email(client):
    """FA-A2: Gross-/Kleinschreibung und Leerzeichen spielen keine Rolle."""
    response = login(client, email="  " + DEMO["email"].upper() + " ")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [
        (DEMO["email"], "falsch"),
        ("unbekannt@pacemaker.ch", DEMO["password"]),
    ],
)
def test_login_failure_gives_same_message(client, email, password):
    """FA-A2: Unbekannte E-Mail und falsches Passwort sind nicht unterscheidbar."""
    response = login(client, email=email, password=password)
    assert response.status_code == 401
    assert response.get_json() == {"error": "E-Mail oder Passwort ist falsch."}


def test_login_requires_both_fields(client):
    response = client.post("/api/auth/login", json={"email": DEMO["email"]})
    assert response.status_code == 400


def test_login_without_json_body(client):
    response = client.post("/api/auth/login", data="kein json")
    assert response.status_code == 400


def test_me_without_session_is_401_json(client):
    """FA-A4: ohne Sitzung kein Zugriff, Antwort als JSON statt Umleitung."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Bitte melde dich an."}


def test_session_survives_requests(client):
    """FA-A2: Die Anmeldung bleibt über mehrere Aufrufe bestehen."""
    login(client)
    assert client.get("/api/auth/me").get_json()["email"] == DEMO["email"]
    assert client.get("/api/auth/me").status_code == 200


def test_logout_ends_session(client):
    """FA-A3: Nach dem Abmelden ist die Sitzung serverseitig beendet."""
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_second_demo_user_can_log_in(client):
    """FA-A1: Beide Demo-Konten funktionieren."""
    second = DEMO_USERS[1]
    response = login(client, email=second["email"], password=second["password"])
    assert response.get_json()["email"] == second["email"]
