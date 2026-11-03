"""Einrichtungskommandos: Tabellen und Anfangsbestand anlegen.

uv run flask --app app init-db
    Löscht alle Tabellen und legt sie neu an (ADR 0003). Danach sind nur die
    Demo-Konten und die Rückfragen vorhanden, keine Läufe. Für lokal.

uv run flask --app app setup-db
    Legt fehlende Tabellen an, den Anfangsbestand nur in eine leere
    Datenbank. Bestehende Daten bleiben erhalten. Läuft auf Render bei jedem
    Start (siehe Dockerfile).
"""

import click
from flask.cli import with_appcontext
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
    seed()


def setup_db():
    """Gibt True zurück, wenn der Anfangsbestand neu angelegt wurde."""
    # create_all legt nur fehlende Tabellen an; bestehende bleiben, wie sie
    # sind. Änderungen am Datenmodell brauchen weiterhin einen Neuaufbau
    # (ADR 0003).
    db.create_all()
    if db.session.scalar(db.select(User.id).limit(1)) is not None:
        return False
    seed()
    return True


def seed():
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
@with_appcontext
def init_db_command():
    """Datenbank neu aufbauen und Demo-Konten sowie Rückfragen anlegen."""
    init_db()
    click.echo(
        f"Datenbank eingerichtet: {len(DEMO_USERS)} Demo-Konten, "
        f"{len(QUESTIONS)} Rückfragen."
    )


@click.command("setup-db")
@with_appcontext
def setup_db_command():
    """Fehlende Tabellen anlegen, Anfangsbestand nur in eine leere Datenbank."""
    if setup_db():
        click.echo("Datenbank war leer: Demo-Konten und Rückfragen angelegt.")
    else:
        click.echo("Datenbank enthält bereits Daten, nichts verändert.")
