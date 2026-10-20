"""Tests für /api/goals (FA-Z1 bis FA-Z5, FA-A5)."""

from datetime import date, datetime, timedelta

import pytest

from app.goals import weekly_km_suggestion
from app.models import Goal, GoalOption, GoalQuestion, Training, User, db

ANSWERS = {
    "goal": "faster",
    "sessions_per_week": "4",
    "weekly_km": 30,
    "restrictions": "Montag Ruhetag",
}
COMPETITION = {
    "name": "Halbmarathon Luzern",
    "race_date": "2026-12-13",
    "distance_km": 21.0975,
    "target_time": "1:45:00",
}


def save(client, answers=None, competition=None):
    return client.put(
        "/api/goals",
        json={
            "answers": ANSWERS if answers is None else answers,
            "competition": competition,
        },
    )


@pytest.mark.parametrize(
    ("method", "url"),
    [("get", "/api/goals/questions"), ("get", "/api/goals"), ("put", "/api/goals")],
)
def test_requires_login(client, method, url):
    assert getattr(client, method)(url).status_code == 401


def test_questions_come_from_database(app, user_client):
    """FA-Z5: Eine in der Datenbank geänderte Option erscheint ohne Codeänderung."""
    with app.app_context():
        option = db.session.scalar(db.select(GoalOption).where(GoalOption.key == "fit"))
        option.label = "gesund bleiben"
        db.session.commit()

    questions = user_client.get("/api/goals/questions").json
    assert [q["key"] for q in questions] == [
        "goal",
        "sessions_per_week",
        "weekly_km",
        "restrictions",
    ]
    assert "gesund bleiben" in [o["label"] for o in questions[0]["options"]]
    assert questions[2]["answer_type"] == "number"
    assert questions[2]["options"] == []


def test_new_user_has_no_answers(user_client):
    assert user_client.get("/api/goals").json == {
        "answers": {},
        "competition": None,
        "weekly_km_suggestion": 0,
    }


def test_save_and_reload_answers(user_client):
    """FA-Z4: Antworten werden gespeichert und beim nächsten Besuch geliefert."""
    response = save(user_client)
    assert response.status_code == 200
    assert user_client.get("/api/goals").json["answers"] == ANSWERS | {
        "weekly_km": 30.0
    }


def test_answers_are_stored_typed(app, user_client):
    """ADR 0003: je Typ eine Wertspalte, Auswahl als Verweis auf die Option."""
    save(user_client)
    with app.app_context():
        user = db.session.scalar(
            db.select(User).where(User.email == "demo@pacemaker.ch")
        )
        goals = {
            g.question_id: g
            for g in db.session.scalars(db.select(Goal).where(Goal.user_id == user.id))
        }
        questions = {q.key: q for q in db.session.scalars(db.select(GoalQuestion))}
        goal = goals[questions["goal"].id]
        assert goal.option_id is not None
        assert (goal.number_value, goal.text_value) == (None, None)
        weekly = goals[questions["weekly_km"].id]
        assert (weekly.option_id, weekly.number_value, weekly.text_value) == (
            None,
            30.0,
            None,
        )


def test_save_again_overwrites(user_client):
    save(user_client)
    save(user_client, ANSWERS | {"sessions_per_week": "6", "restrictions": ""})
    answers = user_client.get("/api/goals").json["answers"]
    assert answers["sessions_per_week"] == "6"
    assert "restrictions" not in answers  # optionale Antwort geleert


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("goal", None),  # Pflichtfrage
        ("goal", "unbekannt"),
        ("sessions_per_week", "8"),
        ("weekly_km", -1),
        ("weekly_km", 251),
        ("weekly_km", "30"),
        ("weekly_km", True),
        ("restrictions", "x" * 201),
    ],
)
def test_invalid_answers_are_rejected(user_client, key, value):
    """FA-Z1 / NFA-3: Grenzen aus der Datenbank, geprüft im Backend."""
    response = save(user_client, ANSWERS | {key: value})
    assert response.status_code == 400
    assert response.json["error"]
    assert user_client.get("/api/goals").json["answers"] == {}  # nichts gespeichert


def test_unknown_question_is_rejected(user_client):
    assert save(user_client, ANSWERS | {"password": "x"}).status_code == 400


def test_competition_is_saved_with_goal_competition(user_client):
    """FA-Z2."""
    response = save(user_client, ANSWERS | {"goal": "competition"}, COMPETITION)
    assert response.status_code == 200
    assert response.json["competition"] == {
        "name": "Halbmarathon Luzern",
        "race_date": "2026-12-13",
        "distance_km": 21.0975,
        "target_time_s": 6300,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("race_date", "13.12.2026"),
        ("distance_km", 15),
        ("target_time", "schnell"),
    ],
)
def test_invalid_competition_is_rejected(user_client, field, value):
    response = save(
        user_client, ANSWERS | {"goal": "competition"}, COMPETITION | {field: value}
    )
    assert response.status_code == 400


def test_competition_required_when_goal_is_competition(user_client):
    assert save(user_client, ANSWERS | {"goal": "competition"}, None).status_code == 400


def test_competition_removed_when_goal_changes(user_client):
    """FA-Z2: Mit einem anderen Ziel wird der Wettkampf nicht mehr geführt."""
    save(user_client, ANSWERS | {"goal": "competition"}, COMPETITION)
    save(user_client, ANSWERS | {"goal": "fit"}, COMPETITION)
    assert user_client.get("/api/goals").json["competition"] is None


def test_weekly_km_suggestion_uses_last_four_weeks(app):
    """FA-Z3: Durchschnitt der letzten 28 Tage, ältere Läufe zählen nicht."""
    today = date(2026, 10, 20)
    with app.app_context():
        user = db.session.scalar(db.select(User))
        for days_ago, km in [(1, 20), (10, 30), (27, 30), (29, 100)]:
            db.session.add(
                Training(
                    user_id=user.id,
                    source="manuell",
                    activity_type="Laufen",
                    start_time=datetime.combine(today, datetime.min.time())
                    - timedelta(days=days_ago),
                    distance_km=km,
                    moving_time_s=km * 360,
                )
            )
        db.session.commit()
        assert weekly_km_suggestion(user.id, today=today) == 20  # 80 km / 4


def test_answers_are_separated_per_user(user_client, other_client):
    """FA-A5."""
    save(user_client, ANSWERS | {"goal": "competition"}, COMPETITION)
    assert other_client.get("/api/goals").json["answers"] == {}
    assert other_client.get("/api/goals").json["competition"] is None
