"""PaceMaker — Flask-Anwendung.

`create_app()` baut die Anwendung zusammen. Gunicorn startet sie über
`gunicorn app:app`, lokal läuft sie mit `flask --app app run --debug`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from . import auth, goals, recommendation, trainings
from .models import db
from .seed import init_db_command

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
        # Ohne DATABASE_URL: SQLite-Datei in instance/ (nicht versioniert).
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL")
        or "sqlite:///pacemaker.db",
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

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    return app


app = create_app()
