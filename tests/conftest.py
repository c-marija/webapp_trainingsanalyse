import pytest

from app import create_app
from app.models import db
from app.seed import init_db


@pytest.fixture
def app():
    """Anwendung mit leerer In-Memory-Datenbank und Anfangsbestand.

    Der Anwendungskontext wird nach dem Einrichten wieder geschlossen. So
    läuft jede Testanfrage wie im echten Betrieb in einem eigenen Kontext,
    und Flask-Login muss den Benutzer aus dem Sitzungs-Cookie laden, statt
    ihn aus der vorherigen Anfrage weiterzuverwenden.
    """
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        init_db()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def app_context(app):
    """Für Tests, die direkt auf die Datenbank zugreifen."""
    with app.app_context():
        yield


@pytest.fixture
def client(app):
    return app.test_client()
