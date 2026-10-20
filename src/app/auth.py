"""Blueprint /api/auth — Anmeldung und Sitzung (FA-A1 bis FA-A5)."""

from flask import Blueprint, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash

from .models import User, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    # Gilt für jede Route mit @login_required, auch in den anderen Blueprints.
    # Ohne diesen Handler würde Flask-Login auf eine Login-Seite umleiten,
    # die es in einer JSON-API nicht gibt.
    return jsonify(error="Bitte melde dich an."), 401


def _user_json(user):
    return {"name": user.name, "email": user.email}


@bp.post("/login")
def login():
    """FA-A2: Anmeldung mit E-Mail und Passwort eines Demo-Kontos."""
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify(error="Bitte gib E-Mail und Passwort ein."), 400

    user = db.session.scalar(db.select(User).where(User.email == email))
    # Dieselbe Meldung für unbekannte E-Mail und falsches Passwort (FA-A2),
    # sonst liesse sich herausfinden, welche Adressen ein Konto haben.
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify(error="E-Mail oder Passwort ist falsch."), 401

    login_user(user)
    return jsonify(_user_json(user))


@bp.post("/logout")
def logout():
    """FA-A3: Sitzung serverseitig beenden."""
    logout_user()
    return "", 204


@bp.get("/me")
@login_required
def me():
    """FA-A4: Wer ist angemeldet?"""
    return jsonify(_user_json(current_user))
