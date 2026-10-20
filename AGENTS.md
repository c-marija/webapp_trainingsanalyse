# PaceMaker — Anweisungen für Coding-Agenten

PaceMaker ist eine Webanwendung zur Analyse von Lauftrainings, entwickelt von
vier Studierenden im Masterstudium Wirtschaftsinformatik. Der Lernzweck steht
über Vollständigkeit: Alles, was entsteht, muss für das Team verständlich und
nachvollziehbar sein.

## Massgebliche Dokumente

Grundlage jeder Umsetzung sind, in dieser Reihenfolge:

 1. `docs/anforderungen.md` — was gebaut wird (Anforderungs-IDs `FA-…`, `NFA-…`)
 2. `docs/architektur.md` — Schichten, Endpunkte, Tabellen
 3. `docs/decisions/` — angenommene Entscheide, insbesondere
    `0001-technologiewahl.md`

Erkenntnisse des Teams stehen in `docs/lerntagebuch/`.

## Stack

 * Backend: Python ≥ 3.13, Flask, Flask-SQLAlchemy, Flask-Login, Gunicorn
 * Frontend: Vue 3 über CDN, kein Build-Schritt (`src/app/static/index.html`)
 * Datenbank: SQLite lokal, PostgreSQL produktiv
 * KI: Gemini Flash, ausschliesslich über `src/app/ki_service.py`
 * Hosting: Render, deployt automatisch bei jedem Push auf `master`
 * Werkzeuge: `uv` für alles rund um Python, `ruff` für Lint und Format,
   `pytest` für Tests

## Ordnerstruktur

```
src/app/
  __init__.py         create_app(); stellt `app` für `gunicorn app:app` bereit
  models.py           alle SQLAlchemy-Modelle (ADR 0003)
  seed.py             Einrichtungskommando init-db, Demo-Konten, Rückfragen
  auth.py             Blueprint /api/auth
  trainings.py        Blueprint /api/trainings
  garmin.py           Auswertung des Garmin-Exports, ohne Datenbank
  validation.py       gemeinsame Eingabeprüfungen (Zahl, Zeit h:mm:ss)
  goals.py            Blueprint /api/goals
  recommendation.py   Blueprint /api/recommendation
  ki_service.py       einzige Stelle, die das Sprachmodell aufruft
  static/index.html   Frontend
tests/                pytest, eine Datei je Blueprint, Fixtures in conftest.py
instance/             lokale SQLite-Datenbank, nicht versioniert
docs/                 Anforderungen, Architektur, Entscheide, Lerntagebuch
```

## Befehle

```
uv sync --locked --all-groups          Umgebung einrichten
uv run flask --app app init-db         Datenbank neu aufbauen (löscht alle Daten)
uv run flask --app app run --debug     lokal starten
uv run pytest                          Tests mit Coverage
uv run ruff check --fix .              Lint
uv run ruff format .                   Formatieren
```

## Konventionen

 * Bezeichner in Code und Datenbank **englisch**. Oberflächentexte,
   Kommentare, Dokumentation und Commit-Messages **deutsch**.
 * API-Fehler immer als JSON `{"error": "…"}` mit passendem Statuscode;
   im Frontend Aufrufe nur über `apiFetch()`.
 * Validierung, Geschäftslogik und Autorisierung gehören ins Backend. Prüfungen
   im Frontend dienen nur dem Bedienkomfort (NFA-3).
 * Jeder Datenbankzugriff auf Läufe, Antworten und Empfehlungen ist auf das
   angemeldete Konto eingeschränkt (FA-A5).
 * Jede neue Route und jede Fachlogik bekommt Tests. Besonders wichtig:
   CSV-Import, Duplikaterkennung, Datentrennung zwischen den Konten. Tests
   laufen gegen eine Attrappe des KI-Service, nie gegen die echte API.
 * Wo Code eine bestimmte Anforderung umsetzt, die ID im Kommentar oder in der
   Commit-Message nennen (z. B. `FA-I4`).
 * Einfach vor elegant: keine Abstraktion, die das Team erst erklären müsste,
   solange die einfache Lösung die Anforderung erfüllt.

## Arbeitsweise

 * Orientiere dich an den Anforderungen. Weicht eine Bitte davon oder von der
   Architektur ab, sprich das an, bevor du umsetzt.
 * **Bist du unsicher, frag nach, statt eine Annahme zu treffen.** Das gilt
   besonders, wenn eine Anforderung unklar oder widersprüchlich ist oder wenn
   es mehrere vertretbare Lösungen mit unterschiedlichen Folgen gibt.
 * Erkläre nach einer Umsetzung kurz, was du gemacht hast und warum — so, dass
   das Team es in der Prüfung wiedergeben könnte.
 * Schlage nach jedem abgeschlossenen Feature einen Eintrag für
   `docs/lerntagebuch/` vor.
 * Neue Technologie- oder Architekturentscheide: zuerst mit dem Team abwägen
   (Skill `.agents/skills/challenge-development-decisions`), dann als Decision
   Record in `docs/decisions/` nach `docs/decision-template.md` festhalten,
   fortlaufend nummeriert.

## Grenzen

Nur nach Rückfrage:

 * neue Dependencies (`uv add`)
 * Änderungen am Datenmodell
 * Änderungen an `docs/anforderungen.md` oder an angenommenen Decision Records
 * Dateien löschen
 * Aufrufe der echten Gemini-API

Git:

 * Committen und pushen nur auf ausdrückliche Aufforderung.
 * Gearbeitet wird auf Feature-Branches. Auf `master` gelangt Code nur über
   einen Pull Request — jeder Push auf `master` löst ein Deployment aus.

Nie:

 * Secrets, `.env` oder die lokale SQLite-Datei committen
 * eine Prüfung ausschliesslich im Frontend umsetzen
