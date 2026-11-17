# Automatische Tests mit GitHub Actions (CI)

Datum: 2026-11-15

## Status

Angenommen. Ersetzt in [0001-technologiewahl.md](0001-technologiewahl.md)
den Punkt *Deployment* („GitHub Actions entfällt") und schliesst das dort
akzeptierte Risiko „Ohne GitHub Actions laufen Tests und Linting nur, wenn
sie jemand lokal ausführt".

## Kontext

Die Anwendung hat rund 150 automatisierte Tests (pytest) und eine Lint- und
Formatprüfung (ruff). Bisher liefen sie nur, wenn jemand daran dachte, sie
lokal zu starten. ADR 0001 hat bewusst auf GitHub Actions verzichtet, um den
Einstieg einfach zu halten, und das Risiko festgehalten: Fehlerhafter Code
kann bis ins Deployment gelangen.

Seither hat sich die Lage verändert:

 * Die Anwendung ist öffentlich erreichbar (NFA-2), jeder Merge auf `master`
   geht live.
 * Der Branch-Schutz (ADR 0002, Nachtrag) erzwingt eine Freigabe durch eine
   zweite Person, prüft aber nicht, ob die Tests grün sind. Wer freigibt,
   sieht den Code, nicht den Testlauf.
 * Beim Austausch mit dem Dozenten zum Testing kam die Rückmeldung, das Team
   solle sich hier vertiefen.

## Geprüfte Optionen

 * **Weiter nur lokal testen** — kein Aufwand. Das Risiko aus ADR 0001 bleibt;
   ob getestet wurde, hängt an der Disziplin jeder einzelnen Person.
 * **GitHub Actions, nur als Anzeige** — Tests laufen automatisch, das
   Ergebnis erscheint im Pull Request. Ein übersehener roter Lauf lässt sich
   trotzdem mergen.
 * **GitHub Actions als Pflicht-Check** — gewählt. Ein roter Lauf sperrt den
   Merge.
 * **Zusätzlich Browser-Tests (Playwright)** — würde das Frontend abdecken,
   das heute nur von Hand getestet wird. Neue Dependency, Browser-Download und
   deutlich mehr Aufwand; für später zurückgestellt.

## Entscheidung

Im Team entschieden am 15.11.2026:

| Frage | Entscheid |
|---|---|
| Werkzeug | GitHub Actions, Datei `.github/workflows/tests.yml` |
| Auslöser | jeder Pull Request und jeder Push auf `master` |
| Prüfungen | `ruff check`, `ruff format --check`, `pytest` mit Coverage |
| Verbindlichkeit | Pflicht-Check „Tests und Lint" im Ruleset von `master`: roter Lauf = kein Merge |
| Deployment | Render deployt erst nach grünem Lauf auf `master` (Auto-Deploy „After CI Checks Pass") |

## Begründung

 * **Aus „wir testen" wird „ungetesteter Code kann nicht live gehen".** Erst
   der Pflicht-Check schliesst das Risiko aus ADR 0001; eine reine Anzeige
   verlässt sich wieder auf Aufmerksamkeit.
 * **Gleiche Prüfung für alle, auch für Coding-Agenten.** Der Lauf hängt
   nicht davon ab, wer den Code geschrieben hat oder ob lokal alles
   eingerichtet ist.
 * **Saubere Umgebung.** Der Lauf startet ohne `.env`, ohne lokale Datenbank
   und ohne API-Schlüssel. Er zeigt, dass die Tests nichts voraussetzen, was
   nur auf einem Rechner im Team vorhanden ist.
 * **Formatierung blockiert mit.** AGENTS.md schreibt ruff vor; ohne Prüfung
   bleibt das eine Empfehlung.
 * **Render wartet auf CI** als zweite Sicherung: Der Stand auf `master` nach
   dem Merge kann sich vom getesteten Stand im Pull Request unterscheiden,
   wenn zwischendurch ein anderer Pull Request gemergt wurde.
 * **Kein Zusatzaufwand bei Kosten und Paketen.** Das Repository ist
   öffentlich, GitHub Actions ist dafür kostenlos. Es braucht keine neue
   Python-Dependency; der Lauf verwendet dieselben Befehle wie lokal.

## Konsequenzen

**Was einfacher wird**

 * Wer einen Pull Request freigibt, sieht am grünen Haken, dass Tests und
   Lint bestanden sind, und kann sich in der Review auf den Inhalt
   konzentrieren.
 * In der Prüfung lässt sich jeder Testlauf auf GitHub unter „Actions"
   belegen.

**Was schwieriger wird**

 * Ein vergessenes `uv run ruff format .` macht den Lauf rot. Behebung: den
   Befehl lokal ausführen und erneut pushen.
 * Jeder Pull Request wartet rund eine Minute auf den Lauf, das Deployment
   startet entsprechend später.
 * Der Name des Checks („Tests und Lint") steht im Ruleset. Wird er in der
   Workflow-Datei geändert, bleibt jeder Pull Request gesperrt, bis das
   Ruleset angepasst ist.
 * Ein Test, der nur manchmal fehlschlägt (z. B. die Zeitmessung aus NFA-6
   auf einem langsamen Server), blockiert den Merge. Ein solcher Test muss
   repariert werden, nicht übersprungen.

**Folgeaufgaben**

 * *Ruleset:* Unter Settings → Rules → Rulesets für `master` „Require status
   checks to pass" aktivieren und den Check „Tests und Lint" hinzufügen.
   Nur mit Admin-Rechten möglich (c-marija). Der Check erscheint in der
   Auswahl erst, nachdem er einmal gelaufen ist.
 * *Render:* Unter Settings → Build & Deploy → Auto-Deploy „After CI Checks
   Pass" wählen.

**Weiterhin offen**

 * Das Frontend ist nicht automatisch getestet. Browser-Tests (z. B.
   Playwright) wären der nächste Schritt.
 * Das Dockerfile und der echte Aufruf der Claude-API werden weiterhin erst
   auf Render bzw. von Hand geprüft.
