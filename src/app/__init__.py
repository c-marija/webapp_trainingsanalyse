"""PaceMaker — Flask-Anwendung.

`create_app()` baut die Anwendung zusammen. Gunicorn startet sie über
`gunicorn app:app`, lokal läuft sie mit `flask --app app run --debug`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

from . import auth, goals, recommendation, trainings
from .models import db
from .seed import init_db_command, setup_db_command

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def database_url():
    """Datenbankadresse aus der Umgebung, ohne Angabe lokales SQLite.

    Render liefert die Adresse als "postgres://…" oder "postgresql://…".
    SQLAlchemy kennt "postgres://" nicht und braucht den Treibernamen,
    damit es psycopg (Version 3) verwendet: "postgresql+psycopg://…".
    """
    # "or" statt Standardwert in get(): auch ein leerer Eintrag in .env
    # fällt auf SQLite zurück (Datei in instance/, nicht versioniert).
    url = os.environ.get("DATABASE_URL") or "sqlite:///pacemaker.db"
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def create_app(test_config=None):
    load_dotenv()

    # static_url_path="" liefert den Prototyp unter "/" aus; die API liegt
    # unter "/api/…" und kommt sich damit nicht in die Quere.
    # instance_path: Ordner für die lokale SQLite-Datei, im Projektverzeichnis
    # statt versteckt neben dem Code.
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
        instance_path=str(PROJECT_ROOT / "instance"),
    )

    app.config.from_mapping(
        # Produktiv zwingend über die Umgebung setzen (NFA-4).
        # "or" statt Standardwert in get(): auch ein leerer Eintrag in .env
        # fällt auf den Standard zurück.
        SECRET_KEY=os.environ.get("SECRET_KEY") or "nur-fuer-lokale-entwicklung",
        SQLALCHEMY_DATABASE_URI=database_url(),
        # Verbindung vor Gebrauch prüfen: Render schliesst ruhende
        # Verbindungen, sonst schlägt die erste Anfrage danach fehl.
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        # Sitzungs-Cookie nicht an Anfragen von fremden Seiten mitsenden
        # (Schutz vor Cross-Site Request Forgery).
        SESSION_COOKIE_SAMESITE="Lax",
        # Obergrenze für hochgeladene Dateien; ein Garmin-Export mit
        # mehreren tausend Läufen ist deutlich kleiner.
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    auth.login_manager.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(trainings.bp)
    app.register_blueprint(goals.bp)
    app.register_blueprint(recommendation.bp)

    app.cli.add_command(init_db_command)
    app.cli.add_command(setup_db_command)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Die Datei ist zu gross (höchstens 5 MB)."), 413

    return app


app = create_app()
