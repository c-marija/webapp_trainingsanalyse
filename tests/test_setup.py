"""Tests für das Grundgerüst: Anwendung, Datenbank, Einrichtungskommando."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from app.models import GoalQuestion, Training, User, db
from app.seed import DEMO_USERS, init_db


def test_index_serves_prototype(client):
    with client.get("/") as response:
        assert response.status_code == 200
        assert b"PaceMaker" in response.data


def test_init_db_creates_two_demo_users_with_hashed_passwords(app_context):
    """FA-A1: zwei Demo-Konten, Passwort nur als Hash."""
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    assert len(users) == 2
    for user, demo in zip(users, DEMO_USERS, strict=True):
        assert user.email == demo["email"]
        assert user.password_hash != demo["password"]
        assert check_password_hash(user.password_hash, demo["password"])


def test_init_db_creates_goal_questions_in_order(app_context):
    """FA-Z1 / FA-Z5: vier Rückfragen mit Typ und Optionen aus der Datenbank."""
    questions = db.session.scalars(
        db.select(GoalQuestion).order_by(GoalQuestion.position)
    ).all()

    assert [q.key for q in questions] == [
        "goal",
        "sessions_per_week",
        "weekly_km",
        "restrictions",
    ]
    goal, sessions, weekly_km, restrictions = questions

    assert [o.label for o in goal.options] == [
        "Wettkampf",
        "schneller werden",
        "mehr Umfang",
        "fit bleiben",
    ]
    assert [o.key for o in sessions.options] == ["2", "3", "4", "5", "6", "7"]
    assert (weekly_km.answer_type, weekly_km.min_value, weekly_km.max_value) == (
        "number",
        0,
        250,
    )
    assert weekly_km.options == []
    assert restrictions.required is False
    assert restrictions.max_length == 200


def test_init_db_can_run_twice(app_context):
    """ADR 0003: Neuaufbau ist der Weg bei Änderungen am Datenmodell."""
    init_db()
    assert db.session.scalar(db.select(db.func.count(User.id))) == 2


def test_sqlite_enforces_foreign_keys(app_context):
    """Ein Lauf ohne existierendes Konto wird abgewiesen, wie in PostgreSQL."""
    db.session.add(
        Training(
            user_id=999,
            source="manuell",
            activity_type="Laufen",
            start_time=datetime(2026, 10, 20, 18, 0),
            distance_km=5.0,
            moving_time_s=1800,
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
