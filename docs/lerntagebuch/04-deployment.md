# Deployment und Betrieb

Erkenntnisse zu Hosting, Konfiguration, Abhängigkeiten und Automatisierung.
Eintragsformat siehe [README.md](README.md).

Typische Fragen, die hier beantwortet werden sollten:

 * Was ist der Unterschied zwischen "läuft bei mir lokal" und "läuft im Betrieb"?
 * Welche Rolle spielt der WSGI/ASGI-Server, und warum reicht der eingebaute
   Entwicklungsserver nicht?
 * Wie verwalten wir Abhängigkeiten reproduzierbar (`uv`, `uv.lock`)?
 * Wo liegen Konfiguration und Geheimnisse, und warum nicht im Repository?
 * Was macht die CI/CD-Pipeline, und was würde ohne sie von Hand passieren?

---

### 2026-11-03 — Lokal läuft ist nicht gleich läuft auf dem Server (Team)

**Ausgangslage:** Lokal funktionierte alles, alle Tests waren grün. Für das
erste Deployment auf Render (NFA-2) mussten wir trotzdem fünf Dinge ändern,
bevor die Anwendung dort überhaupt starten konnte.

**Was wir gelernt haben:**

 * **Ein fehlender Treiber fällt lokal nicht auf.** Python bringt den Treiber
   für SQLite mit, für PostgreSQL nicht. Erst mit der neuen Dependency
   `psycopg` kann SQLAlchemy mit der Datenbank bei Render sprechen.
 * **Dieselbe Angabe, andere Schreibweise.** Render liefert die
   Datenbankadresse als `postgres://…`, SQLAlchemy erwartet
   `postgresql+psycopg://…`. Die Anwendung schreibt sie jetzt selbst um.
 * **Der Webserver hat eigene Grenzen.** Gunicorn bricht eine Anfrage nach
   30 Sekunden ab und bearbeitet standardmässig nur eine Anfrage
   gleichzeitig. Mit `--timeout 180` und `--threads 4` wartet er lange genug
   auf das Sprachmodell, ohne dass alle anderen blockiert sind.
 * **Ein Befehl, der lokal praktisch ist, wäre auf dem Server gefährlich.**
   `init-db` löscht alle Daten. Weil es im Gratisangebot von Render keine
   Konsole gibt, läuft beim Start stattdessen `setup-db`: Es legt nur an, was
   fehlt.
 * **Auto-Deploy macht jeden Merge öffentlich.** Seit Render läuft, ist der
   Pull Request der letzte Kontrollpunkt vor der Öffentlichkeit.

**Was wir daraus gemacht haben:** Alles im Pull Request
`feature/deployment` umgesetzt, mit Tests für die Umschreibung der Adresse
und dafür, dass `setup-db` keine Daten löscht. Geheimnisse
(`DATABASE_URL`, `SECRET_KEY`, API-Schlüssel) stehen nur in den
Umgebungsvariablen von Render, nie im Repository (NFA-4).

**Offen geblieben:** Das Dockerfile konnten wir lokal nicht testen (kein
Docker installiert); geprüft hat es erst der erste Build auf Render. Die
kostenlose Datenbank bei Render läuft nach rund 30 Tagen ab.

**Merksatz:** Grüne Tests beweisen, dass der Code stimmt — nicht, dass die
Umgebung stimmt. Was lokal stillschweigend vorhanden ist (Treiber, Zeit,
eine Konsole), muss man für den Server ausdrücklich einrichten.

