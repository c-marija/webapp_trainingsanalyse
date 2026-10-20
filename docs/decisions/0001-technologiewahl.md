# Technologiewahl für die Trainingsanalyse-Webanwendung

Datum: 2026-10-20

## Status

Angenommen — vom gesamten Team abgenommen am 2026-10-20

## Kontext

Wir entwickeln im Rahmen des Moduls Softwareentwicklung zu viert eine
Webanwendung zur Analyse von Lauftrainings ("PaceMaker"). Die fachlichen
Anforderungen stehen in [../anforderungen.md](../anforderungen.md), der
Aufbau der Anwendung in [../architektur.md](../architektur.md).

Kurz zusammengefasst: Zwei Demo-Konten melden sich an, importieren ihre Läufe
als Garmin-CSV oder erfassen sie von Hand, beantworten Rückfragen zu ihrem
Trainingsziel und erhalten dazu Trainingsempfehlungen eines Sprachmodells.
Die Rückfragen stammen aus der Datenbank; je Konto wird nur die letzte
Empfehlung aufbewahrt. Eine Registrierung und grafische Auswertungen sind
nicht vorgesehen.

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

**Trainingsempfehlungen**

 * **Gemini Flash im kostenlosen Kontingent** — formuliert Empfehlungen in
   natürlicher Sprache, externe Abhängigkeit.
 * **Regelbasierte Logik in Python** — keine externe Abhängigkeit, aber
   deutlich weniger ausdrucksstark.

**Diagramme**

 * **Chart.js über CDN** — kein Build-Schritt, passt zur bestehenden
   Frontend-Architektur. Ursprünglich gewählt, mit dem Verzicht auf
   grafische Auswertungen in den Anforderungen jedoch hinfällig.
 * **Keine Diagramme** — gewählt, siehe *Abweichungen* unten.

## Entscheidung

Im Team gemeinsam entschieden (vier Personen) am 20.10.2026:

| Bereich | Entscheid |
|---|---|
| Frontend | Vue 3 über CDN |
| Backend | Flask mit Flask-SQLAlchemy und Flask-Login, betrieben mit Gunicorn |
| CSV-Import | Python-Standardmodul `csv` |
| Datenbank produktiv | PostgreSQL bei Render |
| Datenbank lokal | SQLite |
| KI | Gemini Flash im kostenlosen Kontingent, gekapselt in `ki_service.py` |
| Hosting | Render Web Service, Region Frankfurt |
| Deployment | Render deployt automatisch bei jedem Push auf `master`; GitHub Actions entfällt |
| Secrets | lokal in `.env`, produktiv als Environment Variables in Render |

### Abweichungen von der ursprünglichen Entscheidungstabelle

Zwei Einträge weichen von der Tabelle ab, die das Team ursprünglich
festgelegt hat. Beide wurden bei der Abnahme vom Team bestätigt.

| Bereich | Ursprünglich | Jetzt | Grund |
|---|---|---|---|
| Frontend | Vue 3 + **Chart.js** über CDN | Vue 3 über CDN | Diagramme sind laut Anforderungen nicht Bestandteil dieser Version (Abschnitt 7). Eine Bibliothek ohne Verwendung wäre toter Code. |
| Deployment | Push auf **`main`** | Push auf **`master`** | Der Hauptbranch des Repositories heisst `master`. Mit `main` würde Render nie ein Deployment auslösen — ohne Fehlermeldung. |

## Begründung

Der bestehende Prototyp ist eine Single-Page-Anwendung, die vom Server
ausschliesslich JSON benötigt. Für diese Aufgabe reicht Flask vollständig
aus, und der geringe Funktionsumfang ist bei fehlender Vorerfahrung ein
Vorteil: Das Team kann das Framework in überschaubarer Zeit vollständig
durchdringen, statt einen grossen Teil davon nur zu benutzen.

Vue 3 über CDN vermeidet jeden Frontend-Build-Schritt. Das entspricht der
Projektvorgabe und erspart vier Personen die Einrichtung einer
Node-Werkzeugkette, die für den Lernzweck nichts beiträgt.

Flask-SQLAlchemy ist die Voraussetzung dafür, lokal mit SQLite und produktiv
mit PostgreSQL arbeiten zu können, ohne zwei Varianten des Datenzugriffs zu
pflegen. Wir nehmen dafür in Kauf, dass wir weniger SQL von Hand schreiben,
als es ohne ORM der Fall wäre.

Flask-Login übernimmt die sicherheitsrelevanten Teile der Sitzungsverwaltung.
Eine Eigenentwicklung wäre lehrreicher gewesen, hätte bei einem Fehler aber
eine echte Sicherheitslücke bedeutet. Die Autorisierung bleibt unabhängig
davon unsere Aufgabe: Jede Route muss selbst prüfen, dass ein Datensatz der
angemeldeten Person gehört. Dass es zwei Demo-Konten gibt, macht genau diese
Prüfung testbar.

Render wurde gegenüber Azure App Service gewählt, weil Web Service und
Datenbank aus einer Hand kommen und das Deployment ohne zusätzliche
Pipeline bei jedem Push erfolgt. Damit entfällt GitHub Actions als eigenes
Thema — ein bewusster Verzicht zugunsten eines einfacheren Einstiegs.

Die Kapselung des Sprachmodells in `ki_service.py` hält den Anbieter an einer
einzigen Stelle austauschbar. Das Team kann ohne API-Schlüssel gegen eine
Attrappe entwickeln, und ein Wechsel auf regelbasierte Empfehlungen oder einen
anderen Anbieter bleibt ohne Änderungen am übrigen Code möglich.

## Konsequenzen

**Was einfacher wird**

 * Kein Frontend-Build, kein Paketmanager ausser `uv`.
 * Deployment ohne eigene Pipeline: Push auf `master` genügt.
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

 * *Render auf `master` einstellen:* Beim Anlegen des Render-Dienstes ist der
   Branch `master` auszuwählen.
 * *Früh deployen:* Wegen der Abweichung SQLite/PostgreSQL deployen wir ab
   dem ersten lauffähigen Stand regelmässig, nicht erst gegen Projektende.
 * *Datenbank reproduzierbar einrichten:* Demo-Konten (FA-A1) und der
   Anfangsbestand der Rückfragen (FA-Z5) stehen nicht im Code, sondern in der
   Datenbank. Sie werden durch ein Einrichtungskommando angelegt, das lokal
   und produktiv gleich funktioniert. Die Passwörter der Demo-Konten werden
   dabei nur als Hash gespeichert.
 * *Kostenloses Kontingent:* Die Bedingungen des Render-Gratisangebots für
   PostgreSQL sind zu prüfen. Bei kostenlosen Datenbanken ist eine
   Laufzeitbegrenzung üblich, nach der die Instanz gelöscht wird. Das
   Einrichtungskommando aus dem vorigen Punkt ist dann der Weg zurück.
 * *Datenschutz:* An Gemini gehen gemäss FA-E2 die Antworten auf die
   Rückfragen, der Wettkampf und die einzelnen Läufe der letzten 12 Wochen —
   jedoch keine Namen, E-Mail-Adressen oder Kontonummern. Bei kostenlosen
   Kontingenten ist davon auszugehen, dass Eingaben beim Anbieter
   weiterverarbeitet werden können. Für die Demo-Konten ist das unkritisch;
   vor einem Einsatz mit echten Personen wäre es neu zu beurteilen.
 * *Versionskontrolle:* Die lokale SQLite-Datei darf nicht versioniert
   werden. `.gitignore` ist vor dem ersten Backend-Commit um die
   entsprechenden Muster zu ergänzen.
 * Eine spätere Umstellung auf regelbasierte Empfehlungen oder einen anderen
   KI-Anbieter erfordert einen neuen Entscheid in diesem Verzeichnis.
