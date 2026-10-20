"""Blueprint /api/auth — Anmeldung und Sitzung (FA-A1 bis FA-A5).

Routen folgen mit dem Feature „Anmeldung": login, logout, me.
"""

from flask import Blueprint
from flask_login import LoginManager

from .models import User, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
