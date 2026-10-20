"""Gemeinsame Prüfungen für Eingaben aus dem Frontend (NFA-3)."""

import re

TIME_PATTERN = re.compile(r"^(\d{1,2}:)?\d{1,2}:\d{2}$")


def is_number(value):
    # bool ist in Python eine Unterklasse von int; true darf nicht als 1 gelten.
    return isinstance(value, int | float) and not isinstance(value, bool)


def parse_time(value):
    """'h:mm:ss' oder 'mm:ss' -> Sekunden (int), sonst None. '0:00' gilt nicht."""
    value = str(value or "").strip()
    if not TIME_PATTERN.match(value):
        return None
    seconds = 0
    for part in value.split(":"):
        seconds = seconds * 60 + int(part)
    return seconds or None
