"""Tests für /api/trainings (FA-I1 bis FA-L7, FA-A5)."""

from io import BytesIO
from pathlib import Path

import pytest

EXPORT = Path(__file__).parent / "data" / "garmin_export.csv"

RUN = {
    "start_time": "2026-10-20T18:00",
    "title": "Abendlauf",
    "distance_km": 10.0,
    "time": "50:00",
    "avg_hr": 150,
}


def upload(client, data=None, name="Activities.csv"):
    data = EXPORT.read_bytes() if data is None else data
    return client.post(
        "/api/trainings/import",
        data={"file": (BytesIO(data), name)},
        content_type="multipart/form-data",
    )


def titles(client, **params):
    return [
        t["title"]
        for t in client.get("/api/trainings", query_string=params).json["trainings"]
    ]


# --- Anmeldung erforderlich -------------------------------------------------


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/api/trainings"),
        ("post", "/api/trainings"),
        ("delete", "/api/trainings/1"),
        ("post", "/api/trainings/import"),
    ],
)
def test_requires_login(client, method, url):
    assert getattr(client, method)(url).status_code == 401


# --- Import -----------------------------------------------------------------


def test_import_counts(user_client):
    """FA-I2, FA-I4, FA-I5: 7 Zeilen -> 4 importiert, je 1 übersprungen."""
    response = upload(user_client)
    assert response.status_code == 200
    assert response.json == {
        "imported": 4,
        "duplicates": 1,  # gleiche Minute, Distanz weniger als 0,05 km daneben
        "not_a_run": 1,  # Radfahren
        "errors": 1,  # ohne Distanz
    }


def test_import_twice_creates_no_duplicates(user_client):
    """FA-I4: Ein zweiter Import derselben Datei ändert nichts."""
    upload(user_client)
    response = upload(user_client)
    assert response.json["imported"] == 0
    assert response.json["duplicates"] == 5
    assert user_client.get("/api/trainings").json["count"] == 4


def test_import_includes_trailrunning_and_treadmill(user_client):
    upload(user_client)
    types = {
        t["activity_type"] for t in user_client.get("/api/trainings").json["trainings"]
    }
    assert types == {"Laufen", "Trailrunning", "Laufbandtraining"}


def test_import_uses_default_title(user_client):
    upload(user_client)
    assert "Lauf" in titles(user_client)


def test_import_rejects_wrong_file(user_client):
    """FA-I6: verständliche Meldung statt technischem Fehler."""
    response = upload(user_client, data=b"Name,Wert\nx,1\n")
    assert response.status_code == 400
    assert "kein Garmin-Export" in response.json["error"]


def test_import_without_file(user_client):
    response = user_client.post("/api/trainings/import")
    assert response.status_code == 400


def test_import_too_large_file(app, user_client):
    app.config["MAX_CONTENT_LENGTH"] = 100
    response = upload(user_client)
    assert response.status_code == 413
    assert "zu gross" in response.json["error"]


# --- Logbuch ----------------------------------------------------------------


def test_list_sorted_by_date_desc_by_default(user_client):
    """FA-L2: Voreinstellung neueste zuerst."""
    upload(user_client)
    trainings = user_client.get("/api/trainings").json["trainings"]
    starts = [t["start_time"] for t in trainings]
    assert starts == sorted(starts, reverse=True)


def test_list_sorted_by_pace(user_client):
    """FA-L2: Tempo wird aus Zeit und Distanz berechnet und ist sortierbar."""
    upload(user_client)
    trainings = user_client.get(
        "/api/trainings", query_string={"sort": "pace", "direction": "asc"}
    ).json["trainings"]
    paces = [t["moving_time_s"] / t["distance_km"] for t in trainings]
    assert paces == sorted(paces)


def test_list_missing_values_last(user_client):
    """Läufe ohne Puls stehen in beiden Richtungen am Ende."""
    upload(user_client)
    for direction in ("asc", "desc"):
        trainings = user_client.get(
            "/api/trainings", query_string={"sort": "avg_hr", "direction": direction}
        ).json["trainings"]
        assert trainings[0]["avg_hr"] is not None
        assert trainings[-1]["avg_hr"] is None


def test_list_rejects_unknown_sort(user_client):
    response = user_client.get("/api/trainings", query_string={"sort": "password_hash"})
    assert response.status_code == 400


def test_create_training(user_client):
    """FA-L4: manuell erfasster Lauf."""
    response = user_client.post("/api/trainings", json=RUN)
    assert response.status_code == 201
    assert response.json["source"] == "manuell"
    assert response.json["moving_time_s"] == 3000
    assert titles(user_client) == ["Abendlauf"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("distance_km", 0.4),
        ("distance_km", 101),
        ("distance_km", True),
        ("distance_km", "10"),
        ("time", "50 Minuten"),
        ("time", "0:00"),
        ("avg_hr", 59),
        ("avg_hr", 221),
        ("title", ""),
        ("title", "x" * 61),
        ("start_time", "gestern"),
    ],
)
def test_create_training_validates_on_server(user_client, field, value):
    """FA-L4 / NFA-3: Grenzen werden im Backend geprüft."""
    response = user_client.post("/api/trainings", json=RUN | {field: value})
    assert response.status_code == 400
    assert response.json["error"]


def test_create_training_without_heart_rate(user_client):
    response = user_client.post("/api/trainings", json=RUN | {"avg_hr": None})
    assert response.status_code == 201
    assert response.json["avg_hr"] is None


def test_delete_training(user_client):
    """FA-L5."""
    training_id = user_client.post("/api/trainings", json=RUN).json["id"]
    assert user_client.delete(f"/api/trainings/{training_id}").status_code == 204
    assert user_client.get("/api/trainings").json["count"] == 0


def test_delete_unknown_training(user_client):
    assert user_client.delete("/api/trainings/999").status_code == 404


# --- Datentrennung (FA-A5) --------------------------------------------------


def test_other_user_does_not_see_trainings(user_client, other_client):
    upload(user_client)
    assert other_client.get("/api/trainings").json["count"] == 0


def test_other_user_cannot_delete_training(user_client, other_client):
    """Eine fremde Id wird behandelt wie eine nicht existierende."""
    training_id = user_client.post("/api/trainings", json=RUN).json["id"]
    response = other_client.delete(f"/api/trainings/{training_id}")
    assert response.status_code == 404
    assert user_client.get("/api/trainings").json["count"] == 1


def test_duplicates_are_checked_per_user(user_client, other_client):
    """Derselbe Export bei einem zweiten Konto ist kein Duplikat."""
    upload(user_client)
    assert upload(other_client).json["imported"] == 4
