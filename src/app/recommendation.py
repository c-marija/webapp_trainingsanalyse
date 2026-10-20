"""Blueprint /api/recommendation — Trainingsempfehlungen (FA-E1 bis FA-E7).

Routen folgen mit dem Feature „Empfehlung": generieren, abrufen.
Das Sprachmodell wird ausschliesslich über ki_service.py aufgerufen.
"""

from flask import Blueprint

bp = Blueprint("recommendation", __name__, url_prefix="/api/recommendation")
