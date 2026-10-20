# Lerntagebuch

Dieses Verzeichnis dokumentiert, **was wir im Lauf des Projekts gelernt haben**
und **warum wir Dinge so gemacht haben, wie wir sie gemacht haben**.

Es dient zwei Zwecken:

 1. Wir halten Erkenntnisse fest, solange sie frisch sind. Drei Monate später
    weiss niemand mehr, warum eine Entscheidung so gefallen ist.
 2. Es ist unsere Grundlage für die mündliche Prüfung, in der wir zu Kontext
    und Erkenntnissen befragt werden.

## Abgrenzung zu `docs/decisions`

| Wo | Was gehört hinein |
|---|---|
| `docs/decisions/` | Die **Entscheidung** selbst: Kontext, geprüfte Optionen, Wahl, Begründung, Konsequenzen. Formal nach `docs/decision-template.md`. |
| `docs/lerntagebuch/` | Der **Lernprozess** dahinter: Was haben wir dabei verstanden, was hat uns überrascht, wo lagen wir falsch, was nehmen wir mit. |

Faustregel: Sobald ein Eintrag eine Architektur-, Technologie- oder
Deployment-Entscheidung beschreibt, legen wir zusätzlich einen Decision Record
an und **verlinken ihn aus dem Tagebuch-Eintrag**. Die Begründung wird nicht
doppelt geschrieben.

## Dateien

 * [01-git-zusammenarbeit.md](01-git-zusammenarbeit.md) — Versionskontrolle, Branching, Teamarbeit zu viert
 * [02-backend.md](02-backend.md) — Python, Webframework, Routing, Datenhaltung
 * [03-frontend.md](03-frontend.md) — HTML/CSS/JavaScript, Darstellung, Interaktion
 * [04-deployment.md](04-deployment.md) — Betrieb, Hosting, Konfiguration, CI/CD
 * [05-arbeitsweise.md](05-arbeitsweise.md) — Projektorganisation, Arbeit mit Coding-Agenten, Werkzeuge

Passt kein Thema, legen wir eine neue Datei mit der nächsten Nummer an und
tragen sie hier nach.

## Wie wir Einträge schreiben

Jeder Eintrag ist eine `###`-Überschrift mit **Datum, Titel und Kürzel** der
Person. Neue Einträge kommen **unten** an die Datei.

Kürzel: `SG` = Simon Gnos, `Team` = gemeinsamer Eintrag, weitere bitte hier
ergänzen.

```markdown
### 2026-10-20 — Kurzer, aussagekräftiger Titel (SG)

**Ausgangslage:** Was war die Situation, welche Frage stand im Raum?

**Was wir gelernt haben:** Die eigentliche Erkenntnis, in ganzen Sätzen.

**Was wir daraus gemacht haben:** Welche konkrete Konsequenz hatte das für das
Projekt? Falls ein Decision Record existiert: hier verlinken.

**Offen geblieben:** Was wir noch nicht verstanden haben oder später klären.

**Merksatz:** Ein Satz, den wir in der Prüfung sagen können.
```

Nicht jedes Feld muss gefüllt sein. Der **Merksatz** sollte es aber immer sein —
genau danach wird in der Prüfung gefragt.

## Praktischer Hinweis zu Git

Weil mehrere Personen in dieselben Dateien schreiben: **vor dem Schreiben
`git pull`, nach dem Schreiben zügig `git commit` und `git push`.** Ein Eintrag,
der drei Tage unversioniert lokal liegt, wird fast sicher zum Merge-Konflikt.

Tagebuch-Einträge kommen wie jede andere Änderung über einen Branch und einen
Pull Request nach `master` (siehe
[0002-branching-und-zusammenarbeit.md](../decisions/0002-branching-und-zusammenarbeit.md)).
Ein eigener kleiner Pull Request nur für den Eintrag ist dabei völlig in
Ordnung.
