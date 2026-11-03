# KI-Anbieter: Claude statt Gemini

Datum: 2026-11-03

## Status

Angenommen. Ersetzt in [0001-technologiewahl.md](0001-technologiewahl.md)
den Punkt *Trainingsempfehlungen* (Gemini Flash im kostenlosen Kontingent).

## Kontext

Die Trainingsempfehlungen (FA-E1 bis FA-E7) kamen bisher von Gemini Flash im
kostenlosen Kontingent. ADR 0001 hält fest, dass ein Wechsel des
KI-Anbieters einen neuen Entscheid braucht.

Nach dem ersten Deployment auf Render (03.11.2026) scheiterten die
Empfehlungen mit **HTTP 503** von Google: Das Modell `gemini-3.8-flash` war
überlastet. Schon beim ersten lokalen Test am 20.10. brauchte es 97 Sekunden
für ein einziges Wort. Das Team will, dass die Empfehlungen verlässlich
funktionieren.

## Geprüfte Optionen

**Anbieter**

 * **Bei Gemini bleiben, älteres Modell** — keine Codeänderung, weiterhin
   kostenlos. Das kostenlose Kontingent bleibt aber ohne Zusicherung zur
   Verfügbarkeit.
 * **Gemini mit bezahltem Kontingent** — bevorzugte Behandlung, aber
   weiterhin derselbe Anbieter, der beim Test ausgefallen ist.
 * **Claude (Anthropic)** — gewählt. Bezahlt ab dem ersten Aufruf, dafür
   ohne Gratis-Warteschlange.

**Modell** (Preise je 1 Mio. Tokens Eingabe / Ausgabe, Stand 03.11.2026)

 * Claude Opus 5.5 — beste Qualität, $4 / $20, grob 3–4 Rappen je
   Empfehlung.
 * Claude Sonnet 5.5 — $2 / $10, grob 1–2 Rappen je Empfehlung.
 * **Claude Haiku 5.5** — gewählt. Kleinstes und schnellstes Modell,
   $0.10 / $0.50, unter 0.1 Rappen je Empfehlung.

**Aufrufweg**

 * **Offizielles SDK `anthropic`** — gewählt. Neue Dependency, dafür
   automatische Wiederholung bei Überlastung (429, 5xx) und klare
   Fehlerklassen.
 * **Weiter mit `urllib`** — keine Dependency, Wiederholungen und
   Fehlerunterscheidung müssten wir selbst bauen.

**Gemini**

 * **Komplett ersetzen** — gewählt.
 * Umschaltbar behalten — mehr Code, Tests und zwei Schlüssel zu pflegen.

## Entscheidung

Im Team entschieden am 03.11.2026:

| Frage | Entscheid |
|---|---|
| Anbieter | Claude von Anthropic, Gemini wird vollständig entfernt |
| Modell | Claude Haiku 5.5 (`claude-haiku-5-5`), festgelegt in `ki_service.py` |
| Aufrufweg | Offizielles Python-SDK `anthropic` |
| Schlüssel | Umgebungsvariable `ANTHROPIC_API_KEY` (lokal `.env`, produktiv Render) |

## Begründung

 * **Verlässlichkeit vor Gratis.** Der Ausfall hat gezeigt, dass ein
   kostenloses Kontingent für eine öffentlich erreichbare Anwendung (NFA-2)
   zu unsicher ist.
 * **Haiku reicht für die Aufgabe.** Eine Empfehlung ist ein kurzer Text aus
   wenigen Angaben, keine schwierige Denkaufgabe. Haiku ist zudem schnell —
   nach den 97 Sekunden mit Gemini ein spürbarer Unterschied — und kostet
   für ein Studienprojekt praktisch nichts.
 * **Das SDK nimmt uns Arbeit ab**, die wir für die Erreichbarkeit sonst
   selbst bauen müssten: Wiederholungen bei Überlastung mit Pausen und
   Fehlerklassen je Ursache.
 * **Die Kapselung hat sich bewährt.** Weil nur `ki_service.py` das
   Sprachmodell aufruft (ADR 0001), betrifft der Wechsel eine Datei und ihre
   Tests. Prompt, Routen und Frontend bleiben unverändert.

## Konsequenzen

 * **Kosten:** Die Claude-API braucht ein Konto mit Guthaben in der Claude
   Console. Ist es aufgebraucht, zeigt die Anwendung „Guthaben aufgebraucht
   (HTTP 402)". Ein Ausgabenlimit in der Console schützt vor Überraschungen.
 * **Neue Dependency** `anthropic` samt eigenen Abhängigkeiten (u. a.
   `httpx2`, `pydantic`).
 * **Zeitgrenze:** Ein Versuch darf 50 Sekunden dauern, das SDK wiederholt
   bis zu zweimal. Zusammen bleibt das unter dem Gunicorn-Timeout von 180
   Sekunden; ein Test sichert das ab.
 * **Datenschutz:** Statt an Google gehen die Angaben aus FA-E2 nun an
   Anthropic, weiterhin ohne Namen, E-Mail-Adressen oder Kontonummern. Für
   die Demo-Konten unkritisch, vor einem Einsatz mit echten Personen neu zu
   beurteilen.
 * **Ablehnungen:** Claude kann eine Anfrage aus Sicherheitsgründen
   ablehnen (`stop_reason` „refusal"). Die Anwendung zeigt dann eine
   Meldung statt einer leeren Empfehlung.
 * **Aufräumen bei Render:** `GEMINI_API_KEY` und `GEMINI_MODEL` entfernen,
   `ANTHROPIC_API_KEY` eintragen. Den Gemini-Schlüssel im Google AI Studio
   löschen.
