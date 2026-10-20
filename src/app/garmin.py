"""Auswertung des Garmin-Connect-Exports Activities.csv (FA-I2 bis FA-I8).

Reine Funktionen ohne Datenbank: Sie wandeln eine CSV-Zeile in ein
Wörterbuch mit den Feldern des Modells Training um.
"""

import csv
import io
from datetime import datetime

# FA-I2: Nur diese Aktivitätstypen sind Läufe.
RUN_TYPES = {"Laufen", "Laufbandtraining", "Trailrunning"}

# FA-I6 / FA-I8: Ohne diese Spalten ist es kein deutscher Garmin-Export.
REQUIRED_COLUMNS = {"Aktivitätstyp", "Datum"}


class GarminImportError(ValueError):
    """Die Datei als Ganzes kann nicht importiert werden."""


def parse_number(value):
    """FA-I7: '3,727' -> 3727.0, "'-5" -> -5.0, '--' oder '' -> None."""
    value = (value or "").strip().lstrip("'")
    if value in ("", "--"):
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def parse_int(value):
    number = parse_number(value)
    return None if number is None else round(number)


def parse_duration(value):
    """FA-I7: 'h:mm:ss', 'mm:ss' oder mit Zehntelsekunden -> Sekunden."""
    value = (value or "").strip()
    if value in ("", "--"):
        return None
    try:
        seconds = 0.0
        for part in value.split(":"):
            seconds = seconds * 60 + float(part)
    except ValueError:
        return None
    return seconds


def parse_pace(value):
    """Tempo 'mm:ss' pro km -> ganze Sekunden pro km."""
    seconds = parse_duration(value)
    return None if seconds is None else round(seconds)


def parse_bool(value):
    """FA-I7: 'true'/'false' und 'Ja'/'Nein' kommen im selben Export vor."""
    value = (value or "").strip().lower()
    if value in ("true", "ja"):
        return True
    if value in ("false", "nein"):
        return False
    return None


def parse_datetime(value):
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def parse_text(value):
    value = (value or "").strip()
    return value or None


# FA-I3: Spalte im Export -> (Feld im Modell Training, Umwandlung)
COLUMNS = {
    "Aktivitätstyp": ("activity_type", parse_text),
    "Datum": ("start_time", parse_datetime),
    "Favorit": ("favorite", parse_bool),
    "Titel": ("title", parse_text),
    "Distanz": ("distance_km", parse_number),
    "Kalorien": ("calories", parse_int),
    "Zeit": ("timer_time_s", parse_duration),
    "Ø Herzfrequenz": ("avg_hr", parse_int),
    "Maximale Herzfrequenz": ("max_hr", parse_int),
    "Aerober TE": ("aerobic_te", parse_number),
    "Ø Schrittfrequenz (Laufen)": ("avg_cadence_spm", parse_int),
    "Max. Schrittfrequenz (Laufen)": ("max_cadence_spm", parse_int),
    "Ø Pace": ("avg_pace_s_per_km", parse_pace),
    "Beste Pace": ("best_pace_s_per_km", parse_pace),
    "Anstieg gesamt": ("total_ascent_m", parse_number),
    "Abstieg gesamt": ("total_descent_m", parse_number),
    "Ø Schrittlänge": ("avg_stride_length_m", parse_number),
    "Durchschnittliches vertikales Verhältnis": (
        "avg_vertical_ratio_pct",
        parse_number,
    ),
    "Ø vertikale Bewegung": ("avg_vertical_oscillation_cm", parse_number),
    "Ø Bodenkontaktzeit": ("avg_ground_contact_time_ms", parse_int),
    "Durchschnittliche SAP": ("avg_gap_s_per_km", parse_pace),
    "Normalized Power® (NP®)": ("normalized_power_w", parse_int),
    "Training Stress Score®": ("training_stress_score", parse_number),
    "Ø Leistung": ("avg_power_w", parse_int),
    "Max. Leistung": ("max_power_w", parse_int),
    "Schritte": ("steps", parse_int),
    "Body Battery Abnahme": ("body_battery_drain", parse_int),
    "Dekompression": ("decompression", parse_bool),
    "Beste Rundenzeit": ("best_lap_time_s", parse_duration),
    "Anzahl der Runden": ("laps", parse_int),
    "Zeit in Bewegung": ("moving_time_s", parse_duration),
    "Verstrichene Zeit": ("elapsed_time_s", parse_duration),
    "Minimale Höhe": ("min_elevation_m", parse_number),
    "Maximale Höhe": ("max_elevation_m", parse_number),
}


def read_rows(data):
    """Bytes einer hochgeladenen Datei -> Liste von Zeilen als Wörterbücher."""
    try:
        # utf-8-sig entfernt eine Byte-Reihenfolge-Markierung am Anfang (FA-I7).
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise GarminImportError(
            "Die Datei ist keine CSV-Datei im erwarteten Format (UTF-8)."
        ) from error

    reader = csv.DictReader(io.StringIO(text))
    header = {name.strip() for name in (reader.fieldnames or [])}
    if not REQUIRED_COLUMNS <= header:
        raise GarminImportError(
            "Das ist kein Garmin-Export: Die Spalten „Aktivitätstyp“ und "
            "„Datum“ fehlen. Unterstützt wird der Export aus Garmin Connect "
            "mit deutscher Spracheinstellung."
        )
    return [
        {(key or "").strip(): value for key, value in row.items()} for row in reader
    ]


def is_run(row):
    return (row.get("Aktivitätstyp") or "").strip() in RUN_TYPES


def to_training_fields(row):
    """Eine Zeile -> Felder für Training, oder None bei fehlender Pflichtangabe."""
    fields = {
        field: convert(row.get(column)) for column, (field, convert) in COLUMNS.items()
    }
    # FA-I3: ersatzweise die Timerzeit, wenn "Zeit in Bewegung" fehlt.
    if fields["moving_time_s"] is None:
        fields["moving_time_s"] = fields["timer_time_s"]
    if fields["title"] is None:
        fields["title"] = "Lauf"

    required = ("activity_type", "start_time", "distance_km", "moving_time_s")
    if any(fields[name] is None for name in required):
        return None
    if fields["distance_km"] <= 0 or fields["moving_time_s"] <= 0:
        return None
    return fields
