"""Blueprint /api/trainings — Logbuch und Garmin-Import (FA-I1 bis FA-L7).

Routen folgen mit den Features „Logbuch" und „CSV-Import":
abrufen, importieren, anlegen, löschen.
"""

from flask import Blueprint

bp = Blueprint("trainings", __name__, url_prefix="/api/trainings")
