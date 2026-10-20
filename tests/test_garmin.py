"""Tests für die Auswertung des Garmin-Exports (FA-I2 bis FA-I8)."""

from datetime import datetime
from pathlib import Path

import pytest

from app import garmin

EXPORT = Path(__file__).parent / "data" / "garmin_export.csv"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("7.06", 7.06),
        ("3,727", 3727.0),  # Komma ist Tausendertrennzeichen
        ("'-5", -5.0),  # Apostroph vor negativen Zahlen
        ("--", None),
        ("", None),
        ("abc", None),
    ],
)
def test_parse_number(value, expected):
    assert garmin.parse_number(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("00:57:21", 3441.0),
        ("05:14:25", 18865.0),
        ("8:08", 488.0),
        ("00:03:44.6", 224.6),  # Zehntelsekunden
        ("--", None),
        ("1:xx", None),
    ],
)
def test_parse_duration(value, expected):
    assert garmin.parse_duration(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("false", False), ("Ja", True), ("Nein", False), ("--", None)],
)
def test_parse_bool_accepts_both_spellings(value, expected):
    assert garmin.parse_bool(value) is expected


def test_columns_cover_all_34_export_columns():
    """FA-I3: keine Spalte wird verworfen."""
    header = EXPORT.read_text(encoding="utf-8-sig").splitlines()[0].split(",")
    assert len(garmin.COLUMNS) == 34
    assert set(garmin.COLUMNS) == set(header)


def test_read_rows_removes_byte_order_mark():
    rows = garmin.read_rows(EXPORT.read_bytes())
    assert "Aktivitätstyp" in rows[0]


def test_read_rows_rejects_other_files():
    """FA-I6 / FA-I8: fremde Datei oder englischer Export wird abgewiesen."""
    with pytest.raises(garmin.GarminImportError, match="kein Garmin-Export"):
        garmin.read_rows(b"Activity Type,Date\nRunning,2026-10-01 18:00:00\n")


def test_read_rows_rejects_non_utf8():
    with pytest.raises(garmin.GarminImportError, match="UTF-8"):
        garmin.read_rows("Aktivitätstyp,Datum\n".encode("cp1252"))


@pytest.mark.parametrize(
    ("activity_type", "expected"),
    [
        ("Laufen", True),
        ("Laufbandtraining", True),
        ("Trailrunning", True),
        ("Trail Run", False),  # so stand es im Prototyp, Garmin schreibt es anders
        ("Radfahren", False),
    ],
)
def test_is_run(activity_type, expected):
    assert garmin.is_run({"Aktivitätstyp": activity_type}) is expected


def test_to_training_fields_converts_full_row():
    row = garmin.read_rows(EXPORT.read_bytes())[0]
    fields = garmin.to_training_fields(row)

    assert fields["start_time"] == datetime(2026, 10, 1, 18, 0, 15)
    assert fields["favorite"] is True
    assert fields["calories"] == 1234
    assert fields["moving_time_s"] == pytest.approx(2970.5)
    assert fields["avg_pace_s_per_km"] == 370
    assert fields["max_elevation_m"] == 1450
    assert fields["body_battery_drain"] == -7
    assert fields["best_lap_time_s"] == pytest.approx(6.2)
    assert fields["decompression"] is False


def test_to_training_fields_falls_back_to_timer_time():
    """FA-I3: ohne "Zeit in Bewegung" gilt die Timerzeit."""
    fields = garmin.to_training_fields(
        {"Aktivitätstyp": "Laufen", "Datum": "2026-10-07 19:00:00"}
        | {"Distanz": "5.00", "Zeit": "00:30:00", "Zeit in Bewegung": "--"}
    )
    assert fields["moving_time_s"] == 1800


def test_to_training_fields_rejects_missing_distance():
    fields = garmin.to_training_fields(
        {"Aktivitätstyp": "Laufen", "Datum": "2026-10-06 18:00:00"}
        | {"Distanz": "--", "Zeit in Bewegung": "00:30:00"}
    )
    assert fields is None
