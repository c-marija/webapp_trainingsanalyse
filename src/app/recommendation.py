"""Blueprint /api/recommendation — Trainingsempfehlungen (FA-E1 bis FA-E7).

Das Sprachmodell wird ausschliesslich über ki_service.py aufgerufen.
"""

from datetime import UTC, date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from . import ki_service
from .goals import current_answers, current_competition, ordered_questions
from .models import Recommendation, Training, db

bp = Blueprint("recommendation", __name__, url_prefix="/api/recommendation")

# FA-E1: vier vorgegebene Fragen
QUESTIONS = [
    {"id": "improve", "text": "Wie kann ich mein Training verbessern?"},
    {
        "id": "goal_realistic",
        "text": "Ist mein Ziel mit meinem aktuellen Training realistisch?",
    },
    {"id": "volume", "text": "Steigere ich meinen Umfang zu schnell?"},
    {"id": "this_week", "text": "Was soll ich diese Woche laufen?"},
]

INSTRUCTIONS = (
    "Du bist ein erfahrener Lauftrainer. Beantworte die Frage einer "
    "Freizeitläuferin oder eines Freizeitläufers auf Deutsch mit Schweizer "
    "Rechtschreibung (ss statt ß). Beziehe dich konkret auf die Daten unten "
    "und nenne Zahlen daraus. Höchstens 200 Wörter, als Fliesstext oder kurze "
    "nummerierte Liste. Reichen die Daten für eine Aussage nicht, sag das. "
    "Stelle keine medizinischen Diagnosen."
)

CONTEXT_WEEKS = 12


def error(message, status=400):
    return jsonify(error=message), status


def recommendation_json(r):
    return {
        "question": r.question,
        "answer": r.answer,
        "prompt": r.context,
        # Gespeichert in UTC ohne Zeitzone; "Z" sagt dem Browser, dass er die
        # Zeit in die lokale Zeitzone umrechnen muss.
        "created_at": r.created_at.isoformat(timespec="seconds") + "Z",
    }


def _format_duration(seconds):
    seconds = round(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes}:{secs:02}"


def _format_number(value):
    return "-" if value is None else f"{value:g}"


def build_context(user_id, today=None):
    """FA-E2: Datenkontext aus Rückfragen, Wettkampf und Läufen der letzten
    12 Wochen. Enthält bewusst weder Name noch E-Mail noch Kontonummer."""
    today = today or date.today()
    lines = ["Rückfragen:"]

    answers = current_answers(user_id)
    for question in ordered_questions():
        value = answers.get(question.key)
        if question.answer_type == "choice" and value is not None:
            value = next((o.label for o in question.options if o.key == value), value)
        elif question.answer_type == "number" and value is not None:
            value = f"{value:g}"
        lines.append(f"- {question.text} {value or 'keine Angabe'}")

    competition = current_competition(user_id)
    if competition is not None:
        lines.append(
            f"Wettkampf: {competition.name}, {competition.race_date:%d.%m.%Y}, "
            f"{competition.distance_km:g} km, "
            f"Zielzeit {_format_duration(competition.target_time_s)}"
        )

    since = datetime.combine(
        today - timedelta(weeks=CONTEXT_WEEKS), datetime.min.time()
    )
    runs = db.session.scalars(
        db.select(Training)
        .where(Training.user_id == user_id, Training.start_time >= since)
        .order_by(Training.start_time.desc())
    ).all()
    lines.append(
        f"Läufe der letzten {CONTEXT_WEEKS} Wochen "
        "(Datum; km; Dauer; Tempo pro km; Ø Puls; Höhenmeter; Art):"
    )
    if not runs:
        lines.append("- keine")
    for t in runs:
        lines.append(
            f"- {t.start_time:%d.%m.%Y}; {t.distance_km:g}; "
            f"{_format_duration(t.moving_time_s)}; "
            f"{_format_duration(t.moving_time_s / t.distance_km)}; "
            f"{_format_number(t.avg_hr)}; {_format_number(t.total_ascent_m)}; "
            f"{t.activity_type}"
        )
    return "\n".join(lines)


def build_prompt(question_text, context):
    return f"{INSTRUCTIONS}\n\nFrage: {question_text}\n\n<daten>\n{context}\n</daten>"


def own_recommendation():
    return db.session.scalar(
        db.select(Recommendation).where(Recommendation.user_id == current_user.id)
    )


@bp.get("/questions")
@login_required
def list_questions():
    """FA-E1."""
    return jsonify(QUESTIONS)


@bp.get("")
@login_required
def get_recommendation():
    """FA-E6: die letzte Empfehlung oder null."""
    r = own_recommendation()
    return jsonify(recommendation=None if r is None else recommendation_json(r))


@bp.post("")
@login_required
def create_recommendation():
    """FA-E2 bis FA-E7: Empfehlung erzeugen und die bisherige überschreiben."""
    data = request.get_json(silent=True) or {}
    question = next((q for q in QUESTIONS if q["id"] == data.get("question_id")), None)
    if question is None:
        return error("Bitte wähle eine der vorgegebenen Fragen.")

    # FA-E7: ohne Läufe und ohne Rückfragen fehlt jede Grundlage.
    has_runs = db.session.scalar(
        db.select(Training.id).where(Training.user_id == current_user.id).limit(1)
    )
    if has_runs is None and not current_answers(current_user.id):
        return error(
            "Für eine Empfehlung braucht es Daten: Importiere deine Läufe oder "
            "beantworte die Rückfragen."
        )

    prompt = build_prompt(question["text"], build_context(current_user.id))
    try:
        answer = ki_service.generate(prompt)
    except ki_service.KiServiceError as e:
        # FA-E5: Die bisherige Empfehlung bleibt unverändert erhalten.
        return error(str(e), 503)

    # FA-E6: höchstens eine Empfehlung je Konto, die neue überschreibt die alte.
    r = own_recommendation()
    if r is None:
        r = Recommendation(user_id=current_user.id)
        db.session.add(r)
    r.question = question["text"]
    r.answer = answer
    r.context = prompt  # FA-E4: genau der Text, der gesendet wurde
    r.created_at = datetime.now(UTC).replace(tzinfo=None)
    db.session.commit()
    return jsonify(recommendation_json(r))
