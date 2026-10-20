"""Blueprint /api/goals — Rückfragen und Wettkampf (FA-Z1 bis FA-Z5).

Fragen und Antwortoptionen kommen aus der Datenbank (FA-Z5). Die Oberfläche
baut das Formular aus GET /api/goals/questions auf.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from .models import Competition, Goal, GoalOption, GoalQuestion, Training, db
from .validation import is_number, parse_time

bp = Blueprint("goals", __name__, url_prefix="/api/goals")

# FA-Z2 / FA-Z5: Die Wettkampfangaben erscheinen, wenn bei dieser Frage diese
# Option gewählt ist. Beide Schlüssel stammen aus seed.py.
GOAL_QUESTION_KEY = "goal"
COMPETITION_OPTION_KEY = "competition"

# FA-Z2: wählbare Wettkampfdistanzen in km
COMPETITION_DISTANCES = (5, 10, 21.0975, 42.195)


def error(message, status=400):
    return jsonify(error=message), status


def ordered_questions():
    return db.session.scalars(
        db.select(GoalQuestion).order_by(GoalQuestion.position)
    ).all()


def question_json(q):
    return {
        "key": q.key,
        "text": q.text,
        "answer_type": q.answer_type,
        "required": q.required,
        "min_value": q.min_value,
        "max_value": q.max_value,
        "max_length": q.max_length,
        "options": [{"key": o.key, "label": o.label} for o in q.options],
    }


def current_answers(user_id):
    """{Frageschlüssel: Wert} der Antworten eines Kontos.

    Der Wert steht je nach Antworttyp in einer anderen Spalte (ADR 0003);
    bei Auswahlfragen wird der Schlüssel der gewählten Option geliefert.
    """
    rows = db.session.execute(
        db.select(GoalQuestion.key, Goal, GoalOption.key)
        .join(Goal, Goal.question_id == GoalQuestion.id)
        .outerjoin(GoalOption, GoalOption.id == Goal.option_id)
        .where(Goal.user_id == user_id)
    )
    answers = {}
    for question_key, goal, option_key in rows:
        if goal.option_id is not None:
            answers[question_key] = option_key
        elif goal.number_value is not None:
            answers[question_key] = goal.number_value
        else:
            answers[question_key] = goal.text_value
    return answers


def current_competition(user_id):
    return db.session.scalar(
        db.select(Competition).where(Competition.user_id == user_id)
    )


def competition_json(c):
    if c is None:
        return None
    return {
        "name": c.name,
        "race_date": c.race_date.isoformat(),
        "distance_km": c.distance_km,
        "target_time_s": c.target_time_s,
    }


def weekly_km_suggestion(user_id, today=None):
    """FA-Z3: Durchschnitt der Wochenkilometer der letzten vier Wochen."""
    today = today or date.today()
    since = datetime.combine(today - timedelta(days=28), datetime.min.time())
    total = db.session.scalar(
        db.select(db.func.coalesce(db.func.sum(Training.distance_km), 0)).where(
            Training.user_id == user_id, Training.start_time >= since
        )
    )
    return round(total / 4)


def goals_json(user_id):
    return {
        "answers": current_answers(user_id),
        "competition": competition_json(current_competition(user_id)),
        "weekly_km_suggestion": weekly_km_suggestion(user_id),
    }


@bp.get("/questions")
@login_required
def list_questions():
    """FA-Z5: Fragen mit Antworttyp und Optionen, in fester Reihenfolge."""
    return jsonify([question_json(q) for q in ordered_questions()])


@bp.get("")
@login_required
def get_goals():
    """FA-Z3, FA-Z4: gespeicherte Antworten, Wettkampf und km-Vorschlag."""
    return jsonify(goals_json(current_user.id))


def validate_answer(question, value):
    """Prüft eine Antwort. Rückgabe: (Spaltenwerte für Goal oder None, Fehler)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        if question.required:
            return None, f"Bitte beantworte: {question.text}"
        return None, None

    if question.answer_type == "choice":
        option = next((o for o in question.options if o.key == value), None)
        if option is None:
            return None, f"Ungültige Auswahl bei: {question.text}"
        return {"option_id": option.id}, None

    if question.answer_type == "number":
        # Fehlende Grenzen gelten als unbeschränkt (neue Fragen ohne Codeänderung).
        low = question.min_value if question.min_value is not None else float("-inf")
        high = question.max_value if question.max_value is not None else float("inf")
        if not is_number(value) or not low <= value <= high:
            return None, f"Bitte gib bei „{question.text}“ eine gültige Zahl an."
        return {"number_value": float(value)}, None

    text = str(value).strip()
    if question.max_length and len(text) > question.max_length:
        return None, (
            f"Die Antwort auf „{question.text}“ ist zu lang "
            f"(höchstens {question.max_length} Zeichen)."
        )
    return {"text_value": text}, None


def validate_competition(data):
    """FA-Z2: Rückgabe (Felder für Competition oder None, Fehler)."""
    if not isinstance(data, dict):
        return None, "Bitte gib die Angaben zum Wettkampf an."
    name = str(data.get("name") or "").strip()
    if not name or len(name) > 60:
        return None, "Der Name des Wettkampfs muss 1 bis 60 Zeichen lang sein."
    try:
        race_date = date.fromisoformat(str(data.get("race_date", "")))
    except ValueError:
        return None, "Bitte gib das Datum des Wettkampfs an."
    distance_km = data.get("distance_km")
    if not is_number(distance_km) or distance_km not in COMPETITION_DISTANCES:
        return None, "Bitte wähle eine der vorgegebenen Wettkampfdistanzen."
    target_time_s = parse_time(data.get("target_time"))
    if target_time_s is None:
        return None, "Die Zielzeit muss im Format h:mm:ss angegeben werden."
    return {
        "name": name,
        "race_date": race_date,
        "distance_km": float(distance_km),
        "target_time_s": target_time_s,
    }, None


@bp.put("")
@login_required
def save_goals():
    """FA-Z4: Antworten speichern. Erst alles prüfen, dann alles schreiben."""
    data = request.get_json(silent=True) or {}
    answers = data.get("answers")
    if not isinstance(answers, dict):
        return error("Keine Antworten übermittelt.")

    questions = ordered_questions()
    unknown = set(answers) - {q.key for q in questions}
    if unknown:
        return error(f"Unbekannte Frage: {', '.join(sorted(unknown))}")

    values = {}
    for question in questions:
        columns, message = validate_answer(question, answers.get(question.key))
        if message:
            return error(message)
        values[question] = columns

    wants_competition = answers.get(GOAL_QUESTION_KEY) == COMPETITION_OPTION_KEY
    competition_fields = None
    if wants_competition:
        competition_fields, message = validate_competition(data.get("competition"))
        if message:
            return error(message)

    # Schreiben: eine Zeile je Konto und Frage (ADR 0003)
    existing = {
        g.question_id: g
        for g in db.session.scalars(
            db.select(Goal).where(Goal.user_id == current_user.id)
        )
    }
    for question, columns in values.items():
        goal = existing.get(question.id)
        if columns is None:
            if goal is not None:
                db.session.delete(goal)
            continue
        if goal is None:
            goal = Goal(user_id=current_user.id, question_id=question.id)
            db.session.add(goal)
        goal.option_id = columns.get("option_id")
        goal.number_value = columns.get("number_value")
        goal.text_value = columns.get("text_value")

    # FA-Z2: ohne Ziel "Wettkampf" wird kein Wettkampf mehr geführt.
    competition = current_competition(current_user.id)
    if competition_fields is None:
        if competition is not None:
            db.session.delete(competition)
    else:
        if competition is None:
            competition = Competition(user_id=current_user.id)
            db.session.add(competition)
        for name, value in competition_fields.items():
            setattr(competition, name, value)

    db.session.commit()
    return jsonify(goals_json(current_user.id))
