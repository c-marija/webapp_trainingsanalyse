# Datenmodell

Datum: 2026-10-20

## Status

Angenommen

## Kontext

Mit dem Flask-Grundgerüst entsteht das Datenmodell in `src/app/models.py`.
Die Architektur ([../architektur.md](../architektur.md)) gibt die Tabellen
`users`, `trainings`, `goal_questions`, `goal_options`, `goals` und
`recommendations` vor. Vier Fragen liess sie offen:

 1. Wie werden die 34 Spalten des Garmin-Exports gespeichert (FA-I3)?
 2. Wo liegen die Wettkampfangaben (FA-Z2)?
 3. Wie speichert `goals` Antworten unterschiedlicher Typen — Auswahl, Zahl,
    Freitext (FA-Z5)?
 4. Was passiert, wenn sich das Datenmodell ändert?

Diese Punkte lassen sich später nur mit Aufwand ändern, weil jedes Feature
auf dem Datenmodell aufbaut.

## Geprüfte Optionen

**1. Garmin-Felder**

 * **Eine breite Tabelle mit einer Spalte je Feld** — jedes Feld direkt
   abfragbar und sortierbar, entspricht eins zu eins FA-I3. Die Tabelle wird
   breit (rund 40 Spalten).
 * **Kernfelder als Spalten, Rest als JSON** — kompakter, aber die Felder im
   JSON lassen sich kaum abfragen, und SQLite und PostgreSQL behandeln JSON
   unterschiedlich.

**2. Wettkampf**

 * **Eigene Tabelle `competitions`** — feste Typen für Datum, Distanz und
   Zielzeit. Die Architektur erhält eine siebte Tabelle.
 * **Als versteckte Zusatzfragen in `goal_questions`** — Architektur bleibt
   unverändert, das Formular wird deutlich komplizierter.

**3. Antworten in `goals`**

 * **Eine Zeile je Konto und Frage mit drei Wertspalten** (`option_id`,
   `number_value`, `text_value`), je nach Antworttyp ist genau eine gefüllt —
   korrekt typisiert, die gewählte Option bleibt per Fremdschlüssel verknüpft.
 * **Eine einzige Textspalte** — einfacher, aber Zahlen werden zu Text und
   der Bezug zur Option geht verloren.

**4. Änderungen am Datenmodell**

 * **Datenbank neu aufbauen** (`db.drop_all()` und `db.create_all()` im
   Einrichtungskommando) — keine zusätzliche Dependency; die Demo-Daten
   entstehen ohnehin neu.
 * **Migrationen mit Flask-Migrate (Alembic)** — Änderungen ohne
   Datenverlust, Standard bei echten Nutzerdaten, aber eine zusätzliche
   Dependency und ein weiteres Konzept.

## Entscheidung

Im Team gemeinsam entschieden (vier Personen) am 20.10.2026, jeweils die
erste Option:

| Frage | Entscheid |
|---|---|
| Garmin-Felder | Tabelle `trainings` mit einer Spalte je Feld |
| Wettkampf | Eigene Tabelle `competitions`, höchstens ein Wettkampf je Konto |
| Antworten | `goals` mit `option_id`, `number_value`, `text_value`; eine Zeile je Konto und Frage |
| Änderungen | Neuaufbau über `flask --app app init-db`, keine Migrationen |

## Begründung

Die breite Tabelle bildet FA-I3 direkt ab: Wer die Anforderung liest, findet
jedes Feld in `models.py` wieder, mit dem Garmin-Spaltennamen als Kommentar.
JSON hätte die Tabelle schmaler gemacht, aber genau die Abfragbarkeit
gekostet, für die wir alle Spalten importieren.

Der Wettkampf hat feste, unterschiedliche Typen (Text, Datum, Kommazahl,
Dauer). In einer allgemeinen Antworttabelle müssten sie als Text gespeichert
und bei jeder Verwendung zurückverwandelt werden.

Drei Wertspalten sind die einfachste Form, Antworten unterschiedlicher Typen
korrekt zu speichern. Bei Auswahlfragen verweist die Antwort auf die Option
selbst, nicht auf ihren Text — ändert sich die Beschriftung einer Option,
bleiben bestehende Antworten gültig.

Auf Migrationen verzichten wir, weil es keine Daten gibt, die einen
Neuaufbau überdauern müssen: Die Demo-Konten und Rückfragen legt das
Einrichtungskommando an, Läufe lassen sich jederzeit neu importieren.

## Konsequenzen

**Was einfacher wird**

 * Das gesamte Datenmodell steht in einer Datei und lässt sich ohne
   Zusatzwissen lesen.
 * Jede Anforderung aus FA-I3 hat eine eindeutige Spalte.
 * Eine Änderung am Modell ist mit einem einzigen Kommando eingespielt.

**Was schwieriger wird**

 * **Jeder Neuaufbau löscht alle Läufe**, lokal wie produktiv. Nach einer
   Modelländerung muss die CSV neu importiert werden.
 * Ein späterer Wechsel zu echten Nutzerdaten erfordert die Einführung von
   Migrationen.
 * Die Regel „genau eine Wertspalte ist gefüllt" prüft die Datenbank nicht;
   das muss der Code in `goals.py` sicherstellen.

**Umgesetzt im Grundgerüst**

 * SQLite prüft Fremdschlüssel nur, wenn sie je Verbindung eingeschaltet
   werden. `models.py` schaltet sie ein, damit sich SQLite wie PostgreSQL
   verhält (Risiko aus ADR 0001).
 * Die lokale Datenbank liegt in `instance/pacemaker.db` und ist über
   `.gitignore` von der Versionierung ausgeschlossen.
