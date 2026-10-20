# Branching und Zusammenarbeit im Team

Datum: 2026-10-20

## Status

Angenommen

## Kontext

Wir arbeiten zu viert im selben Repository auf GitHub. Bisher wurde direkt auf
`master` committet. Mit der Technologiewahl
([0001-technologiewahl.md](0001-technologiewahl.md)) hat sich die Lage
verändert: Render deployt **jeden Push auf `master`** automatisch, und
GitHub Actions entfällt. Es gibt also keine automatische Prüfung zwischen
einem Commit und der öffentlich erreichbaren Anwendung.

Zusätzlich arbeiten wir mit Coding-Agenten, die selbstständig committen und
pushen könnten.

## Geprüfte Optionen

 * **Alle arbeiten direkt auf `master`** — kein Zusatzaufwand, aber jeder
   Push geht ungeprüft in Produktion. Zu viert entstehen häufig abgelehnte
   Pushes („non-fast-forward") und Merge-Konflikte auf dem Hauptbranch.
 * **Feature-Branches mit Pull Request** — jede Aufgabe auf einem eigenen
   Branch, Übernahme nach `master` nur über einen Pull Request. Etwas mehr
   Aufwand je Aufgabe, dafür ein Kontrollpunkt vor jedem Deployment.
 * **Git-Flow mit zusätzlichem `develop`-Branch** — trennt Entwicklung und
   Release, für ein Team von vier Personen ohne Release-Zyklen jedoch
   unnötig komplex.

## Entscheidung

Im Team gemeinsam entschieden (vier Personen) am 20.10.2026:

 * Gearbeitet wird auf **Feature-Branches**, ein Branch je Aufgabe.
   Benennung nach Art der Änderung: `feature/…`, `fix/…`, `docs/…`.
 * Nach `master` gelangen Änderungen **ausschliesslich über einen Pull
   Request**. Das gilt auch für Dokumentation und Lerntagebuch.
 * Coding-Agenten committen und pushen nur auf ausdrückliche Aufforderung
   und nie direkt auf `master` (festgehalten in `AGENTS.md`).

## Begründung

Ausschlaggebend ist die Kopplung von `master` an das Deployment. Ohne
Pipeline ist der Pull Request die einzige Stelle, an der eine Änderung vor
der Veröffentlichung noch einmal angesehen wird.

Feature-Branches verringern ausserdem Konflikte: Jede Person arbeitet
isoliert und holt sich den Stand von `master` dann, wenn es passt — nicht
bei jedem Push der anderen.

Git-Flow löst ein Problem, das wir nicht haben: Es gibt keine geplanten
Releases, sondern nur einen fortlaufend deployten Stand.

## Konsequenzen

**Was einfacher wird**

 * Fehlerhafte Zwischenstände erreichen die öffentliche Anwendung nicht.
 * Die Historie zeigt pro Pull Request zusammenhängend, was wofür geändert
   wurde — nützlich für Lerntagebuch und Prüfung.

**Was schwieriger wird**

 * Jede Aufgabe kostet einige zusätzliche Schritte: Branch anlegen, pushen,
   Pull Request öffnen, mergen, danach `master` lokal aktualisieren.
 * Lang lebende Branches entfernen sich von `master` und erzeugen beim Mergen
   grössere Konflikte. Branches sollen deshalb klein bleiben und zügig
   gemergt werden.

**Offen**

 * Ob jeder Pull Request von einer zweiten Person freigegeben werden muss,
   ist nicht festgelegt. Empfohlen ist es; GitHub kann es über eine
   Branch-Schutzregel auf `master` auch erzwingen.
