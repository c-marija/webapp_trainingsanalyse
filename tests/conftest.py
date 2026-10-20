import pytest

from app import create_app
from app.models import db
from app.seed import init_db


@pytest.fixture
def app():
    """Anwendung mit leerer In-Memory-Datenbank und Anfangsbestand."""
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        init_db()
        yield app
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
