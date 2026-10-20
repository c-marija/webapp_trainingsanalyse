"""Tests für /api/recommendation (FA-E1 bis FA-E7, FA-A5).

ki_service.generate wird durch eine Attrappe ersetzt; die echte API wird nie
aufgerufen.
"""

from datetime import date, datetime, timedelta

import pytest

from app import ki_service
from app.models import Recommendation, Training, User, db
from app.recommendation import build_context
from app.seed import DEMO_USERS


@pytest.fixture
def fake_ki(monkeypatch):
    """Attrappe des Sprachmodells. Merkt sich die gesendeten Prompts."""
    prompts = []

    def generate(prompt):
        prompts.append(prompt)
        return f"Antwort Nr. {len(prompts)}"

    monkeypatch.setattr(ki_service, "generate", generate)
    return prompts


def add_run(client, days_ago, km=10.0, title="Lauf"):
    start = datetime.now() - timedelta(days=days_ago)
    response = client.post(
        "/api/trainings",
        json={
            "start_time": start.strftime("%Y-%m-%dT%H:%M"),
            "title": title,
            "distance_km": km,
            "time": "50:00",
            "avg_hr": 150,
        },
    )
    assert response.status_code == 201


def save_goals(client):
    response = client.put(
        "/api/goals",
        json={
            "answers": {
                "goal": "competition",
                "sessions_per_week": "4",
                "weekly_km": 30,
                "restrictions": "",
            },
            "competition": {
                "name": "Halbmarathon Luzern",
                "race_date": "2026-12-13",
                "distance_km": 21.0975,
                "target_time": "1:45:00",
            },
        },
    )
    assert response.status_code == 200


def ask(client, question_id="improve"):
    return client.post("/api/recommendation", json={"question_id": question_id})


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/api/recommendation/questions"),
        ("get", "/api/recommendation"),
        ("post", "/api/recommendation"),
    ],
)
def test_requires_login(client, method, url):
    assert getattr(client, method)(url).status_code == 401


def test_four_questions(user_client):
    """FA-E1."""
    questions = user_client.get("/api/recommendation/questions").json
    assert len(questions) == 4
    assert questions[0]["text"] == "Wie kann ich mein Training verbessern?"


def test_no_recommendation_yet(user_client):
    assert user_client.get("/api/recommendation").json == {"recommendation": None}


def test_no_data_no_request(user_client, fake_ki):
    """FA-E7: ohne Läufe und Rückfragen wird das Sprachmodell nicht befragt."""
    response = ask(user_client)
    assert response.status_code == 400
    assert "braucht es Daten" in response.json["error"]
    assert fake_ki == []


def test_unknown_question(user_client, fake_ki):
    add_run(user_client, 1)
    assert ask(user_client, "freie Frage").status_code == 400
    assert fake_ki == []


def test_recommendation_is_created_and_returned(user_client, fake_ki):
    """FA-E3, FA-E4: Antwort und genau der gesendete Text."""
    add_run(user_client, 1)
    response = ask(user_client)
    assert response.status_code == 200
    data = response.json
    assert data["answer"] == "Antwort Nr. 1"
    assert data["question"] == "Wie kann ich mein Training verbessern?"
    assert data["prompt"] == fake_ki[0]
    assert data["created_at"].endswith("Z")
    assert user_client.get("/api/recommendation").json["recommendation"] == data


def test_prompt_contains_context(user_client, fake_ki):
    """FA-E2: Rückfragen (mit Beschriftung), Wettkampf, Läufe der letzten 12 Wochen."""
    save_goals(user_client)
    add_run(user_client, 3, km=12.5, title="Neuer Lauf")
    add_run(user_client, 7 * 13, km=33.0, title="Alter Lauf")
    ask(user_client, "goal_realistic")
    prompt = fake_ki[0]

    assert "Frage: Ist mein Ziel mit meinem aktuellen Training realistisch?" in prompt
    assert "Was ist dein Trainingsziel? Wettkampf" in prompt
    assert "Gibt es Einschränkungen? keine Angabe" in prompt
    assert (
        "Wettkampf: Halbmarathon Luzern, 13.12.2026, 21.0975 km, Zielzeit 1:45:00"
        in prompt
    )
    assert "; 12.5; 50:00; 4:00; 150; -; Laufen" in prompt
    assert "33" not in prompt.split("<daten>")[1]  # älter als 12 Wochen


def test_prompt_contains_no_personal_data(user_client, fake_ki):
    """FA-E2: kein Name, keine E-Mail, keine Kontonummer."""
    add_run(user_client, 1)
    ask(user_client)
    demo = DEMO_USERS[0]
    assert demo["email"] not in fake_ki[0]
    assert demo["name"] + " " not in fake_ki[0]


def test_new_recommendation_overwrites_old(app, user_client, fake_ki):
    """FA-E6: höchstens eine Empfehlung je Konto, kein Verlauf."""
    add_run(user_client, 1)
    ask(user_client, "improve")
    ask(user_client, "this_week")
    latest = user_client.get("/api/recommendation").json["recommendation"]
    assert latest["question"] == "Was soll ich diese Woche laufen?"
    assert latest["answer"] == "Antwort Nr. 2"
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Recommendation.id))) == 1


def test_failure_keeps_previous_recommendation(user_client, fake_ki, monkeypatch):
    """FA-E5: verständliche Meldung, die bisherige Empfehlung bleibt."""
    add_run(user_client, 1)
    ask(user_client)

    def generate(prompt):
        raise ki_service.KiServiceError("Das Kontingent ist erschöpft.")

    monkeypatch.setattr(ki_service, "generate", generate)
    response = ask(user_client, "this_week")
    assert response.status_code == 503
    assert response.json == {"error": "Das Kontingent ist erschöpft."}
    assert user_client.get("/api/recommendation").json["recommendation"]["answer"] == (
        "Antwort Nr. 1"
    )


def test_recommendations_are_separated_per_user(user_client, other_client, fake_ki):
    """FA-A5."""
    add_run(user_client, 1)
    ask(user_client)
    assert other_client.get("/api/recommendation").json == {"recommendation": None}


def test_build_context_without_runs(app):
    with app.app_context():
        user = db.session.scalar(db.select(User))
        db.session.add(
            Training(
                user_id=user.id,
                source="manuell",
                activity_type="Laufen",
                start_time=datetime(2020, 1, 1, 8, 0),
                distance_km=5,
                moving_time_s=1500,
            )
        )
        db.session.commit()
        context = build_context(user.id, today=date(2026, 10, 20))
    # Der Lauf von 2020 liegt ausserhalb der 12 Wochen.
    assert context.splitlines()[-1] == "- keine"
