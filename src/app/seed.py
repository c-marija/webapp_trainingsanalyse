"""Einrichtungskommando: Datenbank neu aufbauen und Anfangsbestand anlegen.

Aufruf: uv run flask --app app init-db

Achtung: Löscht alle Tabellen und legt sie neu an (ADR 0003). Danach sind
nur die Demo-Konten und die Rückfragen vorhanden, keine Läufe.
"""

import click
from werkzeug.security import generate_password_hash

from .models import GoalOption, GoalQuestion, User, db

# FA-A1: zwei Demo-Konten. Die Zugangsdaten sind bewusst öffentlich, der
# Prototyp zeigt sie auf der Anmeldeseite an.
DEMO_USERS = [
    {"name": "Demo", "email": "demo@pacemaker.ch", "password": "laufen123"},
    {"name": "Demo Zwei", "email": "demo2@pacemaker.ch", "password": "laufen123"},
]

# FA-Z1 / FA-Z5: Anfangsbestand der Rückfragen.
# Optionen als Liste von (key, label).
QUESTIONS = [
    {
        "key": "goal",
        "text": "Was ist dein Trainingsziel?",
        "answer_type": "choice",
        "options": [
            ("competition", "Wettkampf"),
            ("faster", "schneller werden"),
            ("volume", "mehr Umfang"),
            ("fit", "fit bleiben"),
        ],
    },
    {
        "key": "sessions_per_week",
        "text": "Wie viele Einheiten pro Woche kannst du laufen?",
        "answer_type": "choice",
        "options": [(str(n), str(n)) for n in range(2, 8)],
    },
    {
        "key": "weekly_km",
        "text": "Wie viele Kilometer läufst du aktuell pro Woche?",
        "answer_type": "number",
        "min_value": 0,
        "max_value": 250,
    },
    {
        "key": "restrictions",
        "text": "Gibt es Einschränkungen?",
        "answer_type": "text",
        "required": False,
        "max_length": 200,
    },
]


def init_db():
    db.drop_all()
    db.create_all()

    for user in DEMO_USERS:
        db.session.add(
            User(
                name=user["name"],
                email=user["email"],
                password_hash=generate_password_hash(user["password"]),
            )
        )

    for position, q in enumerate(QUESTIONS, start=1):
        question = GoalQuestion(
            key=q["key"],
            text=q["text"],
            answer_type=q["answer_type"],
            position=position,
            required=q.get("required", True),
            min_value=q.get("min_value"),
            max_value=q.get("max_value"),
            max_length=q.get("max_length"),
        )
        for opt_position, (key, label) in enumerate(q.get("options", []), start=1):
            question.options.append(
                GoalOption(key=key, label=label, position=opt_position)
            )
        db.session.add(question)

    db.session.commit()


@click.command("init-db")
def init_db_command():
    """Datenbank neu aufbauen und Demo-Konten sowie Rückfragen anlegen."""
    init_db()
    click.echo(
        f"Datenbank eingerichtet: {len(DEMO_USERS)} Demo-Konten, "
        f"{len(QUESTIONS)} Rückfragen."
    )
