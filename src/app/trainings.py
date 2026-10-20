"""Blueprint /api/trainings — Logbuch und Garmin-Import (FA-I1 bis FA-L7).

Jede Abfrage ist auf das angemeldete Konto eingeschränkt (FA-A5).
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from . import garmin
from .models import Training, db
from .validation import is_number, parse_time

bp = Blueprint("trainings", __name__, url_prefix="/api/trainings")

# FA-L2: erlaubte Sortierungen. "pace" wird berechnet, nicht gespeichert (FA-L1).
SORT_COLUMNS = {
    "start_time": Training.start_time,
    "title": Training.title,
    "distance_km": Training.distance_km,
    "moving_time_s": Training.moving_time_s,
    "pace": Training.moving_time_s / Training.distance_km,
    "avg_hr": Training.avg_hr,
    "total_ascent_m": Training.total_ascent_m,
}


def training_json(t):
    """Die Felder, die das Logbuch anzeigt (FA-L1)."""
    return {
        "id": t.id,
        "start_time": t.start_time.isoformat(timespec="seconds"),
        "title": t.title,
        "activity_type": t.activity_type,
        "source": t.source,
        "distance_km": t.distance_km,
        "moving_time_s": t.moving_time_s,
        "avg_hr": t.avg_hr,
        "total_ascent_m": t.total_ascent_m,
    }


def error(message, status=400):
    return jsonify(error=message), status


def own_trainings():
    """Ausgangspunkt jeder Abfrage: nur Läufe des angemeldeten Kontos (FA-A5)."""
    return db.select(Training).where(Training.user_id == current_user.id)


@bp.get("")
@login_required
def list_trainings():
    """FA-L1, FA-L2: alle Läufe des Kontos, sortiert."""
    sort = request.args.get("sort", "start_time")
    direction = request.args.get("direction", "desc")
    if sort not in SORT_COLUMNS or direction not in ("asc", "desc"):
        return error("Ungültige Sortierung.")

    column = SORT_COLUMNS[sort]
    order = column.asc() if direction == "asc" else column.desc()
    # Fehlende Werte (z. B. kein Puls) immer ans Ende, Id als Gleichstand-Regel.
    query = own_trainings().order_by(order.nulls_last(), Training.id)
    trainings = db.session.scalars(query).all()
    return jsonify(
        count=len(trainings), trainings=[training_json(t) for t in trainings]
    )


@bp.post("")
@login_required
def create_training():
    """FA-L4: Lauf manuell erfassen. Alle Grenzen werden hier geprüft (NFA-3)."""
    data = request.get_json(silent=True) or {}

    try:
        start_time = datetime.fromisoformat(str(data.get("start_time", "")))
    except ValueError:
        return error("Bitte gib Datum und Uhrzeit an.")

    title = str(data.get("title") or "").strip()
    if not title or len(title) > 60:
        return error("Der Titel muss 1 bis 60 Zeichen lang sein.")

    distance_km = data.get("distance_km")
    if not is_number(distance_km) or not 0.5 <= distance_km <= 100:
        return error("Die Distanz muss zwischen 0,5 und 100 km liegen.")

    moving_time_s = parse_time(data.get("time"))
    if moving_time_s is None:
        return error("Die Zeit muss im Format h:mm:ss oder mm:ss angegeben werden.")

    avg_hr = data.get("avg_hr")
    if avg_hr is not None and (not is_number(avg_hr) or not 60 <= avg_hr <= 220):
        return error("Der Puls muss zwischen 60 und 220 liegen.")

    training = Training(
        user_id=current_user.id,
        source="manuell",
        activity_type="Laufen",
        start_time=start_time,
        title=title,
        distance_km=float(distance_km),
        moving_time_s=moving_time_s,
        avg_hr=None if avg_hr is None else round(avg_hr),
    )
    db.session.add(training)
    db.session.commit()
    return jsonify(training_json(training)), 201


@bp.delete("/<int:training_id>")
@login_required
def delete_training(training_id):
    """FA-L5: Lauf löschen, nur wenn er zum Konto gehört (FA-A5)."""
    training = db.session.scalar(own_trainings().where(Training.id == training_id))
    # Fremde und nicht existierende Läufe sind nicht unterscheidbar.
    if training is None:
        return error("Lauf nicht gefunden.", 404)
    db.session.delete(training)
    db.session.commit()
    return "", 204


@bp.post("/import")
@login_required
def import_csv():
    """FA-I1 bis FA-I8: Activities.csv aus Garmin Connect importieren."""
    file = request.files.get("file")
    if file is None:
        return error("Bitte wähle eine CSV-Datei aus.")

    try:
        rows = garmin.read_rows(file.read())
    except garmin.GarminImportError as e:
        return error(str(e))

    # FA-I4: bestehende Läufe einmal laden, nach Startminute gruppiert.
    known = {}
    for start_time, distance_km in db.session.execute(
        db.select(Training.start_time, Training.distance_km).where(
            Training.user_id == current_user.id
        )
    ):
        known.setdefault(_minute(start_time), []).append(distance_km)

    result = {"imported": 0, "duplicates": 0, "not_a_run": 0, "errors": 0}
    for row in rows:
        if not garmin.is_run(row):
            result["not_a_run"] += 1
            continue
        fields = garmin.to_training_fields(row)
        if fields is None:
            result["errors"] += 1
            continue
        same_minute = known.setdefault(_minute(fields["start_time"]), [])
        if any(abs(d - fields["distance_km"]) < 0.05 for d in same_minute):
            result["duplicates"] += 1
            continue

        db.session.add(Training(user_id=current_user.id, source="garmin_csv", **fields))
        same_minute.append(fields["distance_km"])
        result["imported"] += 1

    db.session.commit()
    return jsonify(result)


def _minute(value):
    return value.replace(second=0, microsecond=0)
