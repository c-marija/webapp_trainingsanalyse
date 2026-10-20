# Technologiewahl für die Trainingsanalyse-Webanwendung

Datum: 2026-10-20

## Status

Angenommen

## Kontext

Wir entwickeln im Rahmen des Moduls Softwareentwicklung zu viert eine
Webanwendung zur Analyse von Lauftrainings ("PaceMaker"). Angemeldete
Personen sollen ihre Läufe erfassen oder als Garmin-CSV importieren, ihr
Wettkampfziel hinterlegen und daraus Auswertungen sowie Trainingstipps
erhalten.

Ein funktionsfähiger Frontend-Prototyp existiert bereits als einzelne Datei
`src/app/static/index.html`. Er ist mit Vue 3 über CDN gebaut und arbeitet
gegen ein Mock-Objekt `api` im Browser; die Daten verschwinden beim Neuladen
der Seite. Das Backend besteht noch aus dem WSGI-Stub des Projekttemplates.

Randbedingungen für die Entscheidung:

 * Der Lernzweck steht im Vordergrund, nicht Skalierbarkeit oder
   langfristige Wartbarkeit.
 * Keine Person im Team hat nennenswerte Vorerfahrung mit Webframeworks.
 * Die Anwendung muss öffentlich erreichbar deployt werden.
 * Es stehen keine Budgetmittel zur Verfügung; alle Dienste müssen in einem
   kostenlosen Kontingent nutzbar sein.
 * Die Projektvorgabe verlangt ein Backend vollständig in Python und
   empfiehlt, mit einfachen Lösungen zu beginnen.

## Geprüfte Optionen

**Backend-Framework**

 * **Flask** — kleiner Funktionsumfang, in kurzer Zeit zu verstehen, sehr
   gute Dokumentation, passt zu einer Anwendung, die im Wesentlichen JSON
   ausliefert. Weniger eingebaute Hilfsmittel als die Alternativen.
 * **FastAPI** — automatische Eingabevalidierung und API-Dokumentation,
   dafür zusätzlicher Lernaufwand durch async und Pydantic.
 * **Django** — vollständiges Ökosystem mit Admin-Oberfläche und ORM, für
   den Umfang dieses Projekts deutlich überdimensioniert.

**Datenhaltung**

 * **SQLite lokal, PostgreSQL produktiv** — lokal ohne Installation
   lauffähig, produktiv eine echte Serverdatenbank.
 * **Durchgängig SQLite** — einfachste Variante, auf gehosteten Plattformen
   mit nicht-persistentem Dateisystem jedoch unzuverlässig.
 * **Durchgängig PostgreSQL** — keine Abweichung zwischen den Umgebungen,
   erfordert lokal aber eine Installation oder Docker auf vier Rechnern.

**Datenbankzugriff**

 * **Flask-SQLAlchemy (ORM)** — Datenmodell als Python-Klassen, Datenbank
   austauschbar, dadurch erst der Mischbetrieb SQLite/PostgreSQL praktikabel.
 * **`sqlite3` mit handgeschriebenem SQL** — lehrreicher in Bezug auf SQL,
   aber direkt an SQLite gebunden.

**Anmeldung**

 * **Flask-Login** — etablierte Erweiterung, Sitzungsverwaltung und
   Zugriffsschutz für Routen bereits enthalten.
 * **Eigene Session-Logik über `flask.session`** — lehrreicher, aber
   fehleranfällig bei sicherheitsrelevanten Details.

**Hosting und Deployment**

 * **Render** — kostenloses Kontingent für Web Service und PostgreSQL,
   Deployment automatisch bei jedem Push, Region Frankfurt.
 * **Azure App Service** — im Projekttemplate dokumentiert, erfordert aber
   mehr Konfigurationsschritte und eine separate Datenbank.
 * **Eigener Container** — maximale Kontrolle, zusätzlicher Lernaufwand
   ohne Nutzen für den Projektzweck.

**Trainingstipps**

 * **Gemini Flash im kostenlosen Kontingent** — formuliert Tipps in
   natürlicher Sprache, externe Abhängigkeit.
 * **Regelbasierte Logik in Python** — keine externe Abhängigkeit, aber
   deutlich weniger ausdrucksstark.

**Diagramme**

 * **Chart.js über CDN** — kein Build-Schritt, passt zur bestehenden
   Frontend-Architektur.
 * **Eigene SVG-Darstellung** — volle Kontrolle, hoher Aufwand.

## Entscheidung

Im Team gemeinsam entschieden (vier Personen) am 20.10.2026:

| Bereich | Entscheid |
|---|---|
| Frontend | Vue 3 über CDN, Diagramme mit Chart.js über CDN |
| Backend | Flask mit Flask-SQLAlchemy und Flask-Login, betrieben mit Gunicorn |
| CSV-Import | Python-Standardmodul `csv` |
| Datenbank produktiv | PostgreSQL bei Render |
| Datenbank lokal | SQLite |
| KI | Gemini Flash im kostenlosen Kontingent, gekapselt in `ki_service.py` |
| Hosting | Render Web Service, Region Frankfurt |
| Deployment | Render deployt automatisch bei jedem Push; GitHub Actions entfällt |
| Secrets | lokal in `.env`, produktiv als Environment Variables in Render |

## Begründung

Der bestehende Prototyp ist eine Single-Page-Anwendung, die vom Server
ausschliesslich JSON benötigt. Für diese Aufgabe reicht Flask vollständig
aus, und der geringe Funktionsumfang ist bei fehlender Vorerfahrung ein
Vorteil: Das Team kann das Framework in überschaubarer Zeit vollständig
durchdringen, statt einen grossen Teil davon nur zu benutzen.

Vue 3 und Chart.js über CDN vermeiden jeden Frontend-Build-Schritt. Das
entspricht der Projektvorgabe und erspart vier Personen die Einrichtung
einer Node-Werkzeugkette, die für den Lernzweck nichts beiträgt.

Flask-SQLAlchemy ist die Voraussetzung dafür, lokal mit SQLite und produktiv
mit PostgreSQL arbeiten zu können, ohne zwei Varianten des Datenzugriffs zu
pflegen. Wir nehmen dafür in Kauf, dass wir weniger SQL von Hand schreiben,
als es ohne ORM der Fall wäre.

Flask-Login übernimmt die sicherheitsrelevanten Teile der Sitzungsverwaltung.
Eine Eigenentwicklung wäre lehrreicher gewesen, hätte bei einem Fehler aber
eine echte Sicherheitslücke bedeutet. Die Autorisierung bleibt unabhängig
davon unsere Aufgabe: Jede Route muss selbst prüfen, dass ein Datensatz der
angemeldeten Person gehört.

Render wurde gegenüber Azure App Service gewählt, weil Web Service und
Datenbank aus einer Hand kommen und das Deployment ohne zusätzliche
Pipeline bei jedem Push erfolgt. Damit entfällt GitHub Actions als eigenes
Thema — ein bewusster Verzicht zugunsten eines einfacheren Einstiegs.

Die Kapselung des Sprachmodells in `ki_service.py` hält den Anbieter an einer
einzigen Stelle austauschbar. Das Team kann ohne API-Schlüssel gegen eine
Attrappe entwickeln, und ein Wechsel auf regelbasierte Tipps oder einen
anderen Anbieter bleibt ohne Änderungen am übrigen Code möglich.

## Konsequenzen

**Was einfacher wird**

 * Kein Frontend-Build, kein Paketmanager ausser `uv`.
 * Deployment ohne eigene Pipeline: Push auf den Hauptbranch genügt.
 * Lokale Entwicklung ohne Datenbankinstallation auf vier Rechnern.
 * Das Datenmodell ist an einer Stelle als Python-Klassen beschrieben.

**Was schwieriger wird**

 * Lokale Umgebung und Produktivumgebung verwenden unterschiedliche
   Datenbanken. SQLite erzwingt Fremdschlüssel standardmässig nicht, ist bei
   Datentypen nachlässig und unterstützt `ALTER TABLE` nur eingeschränkt.
   Eine Schemaänderung kann lokal funktionieren und produktiv scheitern.
 * Durch das ORM schreiben wir weniger SQL selbst und lernen entsprechend
   weniger über Abfrageoptimierung.
 * Ohne GitHub Actions laufen Tests und Linting nur, wenn sie jemand lokal
   ausführt. Fehlerhafter Code kann bis ins Deployment gelangen.
 * Mit Flask-Login bleibt die Sitzungsverwaltung teilweise eine Blackbox.

**Akzeptierte Risiken und Folgeaufgaben**

 * *Branch-Name:* Der Hauptbranch des Repositories heisst `master`. Der
   Render-Dienst muss auf diesen Branch konfiguriert werden, sonst wird kein
   Deployment ausgelöst.
 * *Früh deployen:* Wegen der Abweichung SQLite/PostgreSQL deployen wir ab
   dem ersten lauffähigen Stand regelmässig, nicht erst gegen Projektende.
 * *Kostenloses Kontingent:* Die Bedingungen des Render-Gratisangebots für
   PostgreSQL sind zu prüfen. Bei kostenlosen Datenbanken ist eine
   Laufzeitbegrenzung üblich, nach der die Instanz gelöscht wird. Wir
   benötigen einen Weg, den Datenbestand bei Bedarf neu aufzubauen.
 * *Datenschutz:* An Gemini werden ausschliesslich Aggregate übermittelt
   (Wochenkilometer, Pace-Entwicklung, Wettkampfziel), keine Namen,
   E-Mail-Adressen oder vollständigen Rohdatensätze. Bei kostenlosen
   Kontingenten ist davon auszugehen, dass Eingaben beim Anbieter
   weiterverarbeitet werden können.
 * *Versionskontrolle:* Die lokale SQLite-Datei darf nicht versioniert
   werden. `.gitignore` ist vor dem ersten Backend-Commit um die
   entsprechenden Muster zu ergänzen.
 * Eine spätere Umstellung auf regelbasierte Trainingstipps oder einen
   anderen KI-Anbieter erfordert einen neuen Entscheid in diesem Verzeichnis.
