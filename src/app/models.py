"""Datenmodell von PaceMaker.

Alle Tabellen an einer Stelle. Entscheide dazu: docs/decisions/0003-datenmodell.md
"""

import sqlite3
from datetime import UTC, datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite prüft Fremdschlüssel nur, wenn man es bei jeder Verbindung
    # einschaltet. Ohne das verhielte sich SQLite anders als PostgreSQL
    # (Risiko aus ADR 0001).
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _now():
    return datetime.now(UTC)


class User(UserMixin, db.Model):
    """Demo-Konto (FA-A1). Passwort nur als Hash."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)


class Training(db.Model):
    """Ein Lauf. Alle 34 Spalten des Garmin-Exports (FA-I3).

    Zeiten und Tempi in Sekunden, Tempi in Sekunden pro Kilometer.
    Im Kommentar steht jeweils der Spaltenname im Garmin-Export.
    """

    __tablename__ = "trainings"
    __table_args__ = (db.Index("ix_trainings_user_start", "user_id", "start_time"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # "garmin_csv" oder "manuell"

    # Grunddaten
    activity_type = db.Column(db.String(40), nullable=False)  # Aktivitätstyp
    start_time = db.Column(db.DateTime, nullable=False)  # Datum
    title = db.Column(db.String(120), nullable=False, default="Lauf")  # Titel
    favorite = db.Column(db.Boolean)  # Favorit
    distance_km = db.Column(db.Float, nullable=False)  # Distanz
    calories = db.Column(db.Integer)  # Kalorien

    # Zeiten
    moving_time_s = db.Column(db.Float, nullable=False)  # Zeit in Bewegung
    timer_time_s = db.Column(db.Float)  # Zeit
    elapsed_time_s = db.Column(db.Float)  # Verstrichene Zeit
    laps = db.Column(db.Integer)  # Anzahl der Runden
    best_lap_time_s = db.Column(db.Float)  # Beste Rundenzeit

    # Tempo
    avg_pace_s_per_km = db.Column(db.Integer)  # Ø Pace
    best_pace_s_per_km = db.Column(db.Integer)  # Beste Pace
    avg_gap_s_per_km = db.Column(db.Integer)  # Durchschnittliche SAP

    # Herzfrequenz und Belastung
    avg_hr = db.Column(db.Integer)  # Ø Herzfrequenz
    max_hr = db.Column(db.Integer)  # Maximale Herzfrequenz
    aerobic_te = db.Column(db.Float)  # Aerober TE
    training_stress_score = db.Column(db.Float)  # Training Stress Score®
    body_battery_drain = db.Column(db.Integer)  # Body Battery Abnahme

    # Höhe
    total_ascent_m = db.Column(db.Float)  # Anstieg gesamt
    total_descent_m = db.Column(db.Float)  # Abstieg gesamt
    min_elevation_m = db.Column(db.Float)  # Minimale Höhe
    max_elevation_m = db.Column(db.Float)  # Maximale Höhe

    # Laufdynamik
    avg_cadence_spm = db.Column(db.Integer)  # Ø Schrittfrequenz (Laufen)
    max_cadence_spm = db.Column(db.Integer)  # Max. Schrittfrequenz (Laufen)
    avg_stride_length_m = db.Column(db.Float)  # Ø Schrittlänge
    avg_vertical_ratio_pct = db.Column(db.Float)  # Durchschn. vertikales Verhältnis
    avg_vertical_oscillation_cm = db.Column(db.Float)  # Ø vertikale Bewegung
    avg_ground_contact_time_ms = db.Column(db.Integer)  # Ø Bodenkontaktzeit
    steps = db.Column(db.Integer)  # Schritte

    # Leistung
    avg_power_w = db.Column(db.Integer)  # Ø Leistung
    max_power_w = db.Column(db.Integer)  # Max. Leistung
    normalized_power_w = db.Column(db.Integer)  # Normalized Power® (NP®)

    # Sonstiges
    decompression = db.Column(db.Boolean)  # Dekompression


class GoalQuestion(db.Model):
    """Eine Rückfrage (FA-Z5). Antworttyp: choice, number oder text."""

    __tablename__ = "goal_questions"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(40), nullable=False, unique=True)
    text = db.Column(db.String(200), nullable=False)
    answer_type = db.Column(db.String(10), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    required = db.Column(db.Boolean, nullable=False, default=True)
    min_value = db.Column(db.Float)  # nur bei number
    max_value = db.Column(db.Float)  # nur bei number
    max_length = db.Column(db.Integer)  # nur bei text

    options = db.relationship(
        "GoalOption", back_populates="question", order_by="GoalOption.position"
    )


class GoalOption(db.Model):
    """Eine Antwortoption einer Auswahlfrage (FA-Z5)."""

    __tablename__ = "goal_options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(
        db.Integer, db.ForeignKey("goal_questions.id"), nullable=False
    )
    key = db.Column(db.String(40), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    question = db.relationship("GoalQuestion", back_populates="options")


class Goal(db.Model):
    """Antwort eines Kontos auf eine Rückfrage (FA-Z4).

    Je nach Antworttyp der Frage ist genau eine der drei Wertspalten gefüllt.
    """

    __tablename__ = "goals"
    __table_args__ = (db.UniqueConstraint("user_id", "question_id"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    question_id = db.Column(
        db.Integer, db.ForeignKey("goal_questions.id"), nullable=False
    )
    option_id = db.Column(db.Integer, db.ForeignKey("goal_options.id"))
    number_value = db.Column(db.Float)
    text_value = db.Column(db.String(200))


class Competition(db.Model):
    """Wettkampf eines Kontos (FA-Z2). Höchstens einer je Konto."""

    __tablename__ = "competitions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    name = db.Column(db.String(60), nullable=False)
    race_date = db.Column(db.Date, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    target_time_s = db.Column(db.Integer, nullable=False)


class Recommendation(db.Model):
    """Letzte Empfehlung eines Kontos (FA-E6). Eine neue überschreibt sie."""

    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text, nullable=False)  # an das Sprachmodell gesendet (FA-E4)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)
