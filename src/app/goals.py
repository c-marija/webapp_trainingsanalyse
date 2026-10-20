"""Blueprint /api/goals — Rückfragen und Wettkampf (FA-Z1 bis FA-Z5).

Routen folgen mit dem Feature „Ziele erfassen": Fragen abrufen,
Antworten abrufen und speichern.
"""

from flask import Blueprint

bp = Blueprint("goals", __name__, url_prefix="/api/goals")
