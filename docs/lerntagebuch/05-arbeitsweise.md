# Arbeitsweise und Werkzeuge

Erkenntnisse zur Projektorganisation, zur Arbeit mit Coding-Agenten und zu den
eingesetzten Werkzeugen. Eintragsformat siehe [README.md](README.md).

Typische Fragen, die hier beantwortet werden sollten:

 * Wie haben wir die Arbeit zu viert aufgeteilt, und was hat daran funktioniert
   oder nicht funktioniert?
 * Wo hat uns ein Coding-Agent geholfen, wo hat er uns in die Irre geführt?
 * Was haben wir ungeprüft übernommen, und was ist uns dabei passiert?
 * Welche Entscheidung haben wir im Nachhinein anders getroffen — und warum?
 * Welche Werkzeuge (VS Code, uv, GitHub) haben wir kennengelernt, und wofür
   sind sie jeweils zuständig?

Siehe auch [../agent-collaboration.md](../agent-collaboration.md).

---

### 2026-10-20 — Mit Claude Code Feature für Feature entwickeln (Team)

**Ausgangslage:** Wir haben die Anwendung zu viert mit Claude Code als
Coding-Agent aufgebaut — vom leeren Template bis zu Anmeldung, Logbuch,
Rückfragen und KI-Empfehlungen an einem Tag.

**Was wir gelernt haben:**

 * **Die Grundlagen haben wir selbst erarbeitet.** Die Anforderungen
   (`docs/anforderungen.md`) und die Technologiewahl
   (`docs/decisions/0001-technologiewahl.md`) haben wir manuell erstellt und
   validiert. Claude hat Entwürfe geliefert und Widersprüche aufgezeigt, die
   Entscheide aber haben wir getroffen und abgenommen.
 * **Auf dieser Basis lief die Umsetzung sehr gut.** Weil klar war, *was*
   gebaut wird und *womit*, konnte Claude Feature für Feature entwickeln, ohne
   dass wir jede Einzelheit neu besprechen mussten. Rückfragen kamen nur noch
   dort, wo die Anforderungen tatsächlich etwas offenliessen (z. B. wie das
   Frontend während der Umstellung benutzbar bleibt).
 * **Claude Code führt gut durch die Schritte** und erklärt Änderungen und Code
   verständlich — auch Git-Grundlagen, Pull Requests und Fehlerursachen.
 * **Die Regeln in `AGENTS.md` wirken.** Rückfragen vor neuen Dependencies,
   Datenmodelländerungen und echten KI-Aufrufen kamen zuverlässig. Claude hat
   eine neue Dependency sogar bewusst vermieden (Gemini per `urllib` statt
   Bibliothek), statt sie ohne Rückfrage einzuführen.
 * **Claude hat eigene Fehler gefunden und offengelegt**, z. B. einen Test, der
   aus dem falschen Grund grün war, oder einen Shell-Befehl, der die
   Commit-Messages verstümmelte. Prüfen müssen wir trotzdem selbst: Den
   Browser konnte Claude nicht bedienen, das Durchklicken blieb unsere Aufgabe.

**Was wir daraus gemacht haben:** Jedes Feature lief nach demselben Muster:
eigener Branch → Umsetzung mit Tests → Pull Request mit Prüfliste → Review und
Merge durch das Team. Entscheide, die Claude selbst treffen musste, stehen in
der Beschreibung des jeweiligen Pull Requests.

**Offen geblieben:** Wie gut das Muster trägt, wenn mehrere von uns
gleichzeitig mit Claude an verschiedenen Features arbeiten.

**Merksatz:** Ein Coding-Agent ist so gut wie die Vorgaben, die er bekommt.
Anforderungen und Technologiewahl selbst zu erarbeiten und abzunehmen war die
Voraussetzung dafür, dass die Umsetzung danach schnell und nachvollziehbar
ging.

---

### 2026-10-20 — Ein grüner Test prüft nicht automatisch das Richtige (Team)

**Ausgangslage:** Bei der Anmeldung waren alle Tests grün, auch der Test
„die Anmeldung bleibt über mehrere Aufrufe bestehen".

**Was wir gelernt haben:** Die Coverage-Auswertung zeigte, dass die Funktion,
die den Benutzer aus dem Sitzungs-Cookie lädt (`load_user`), nie aufgerufen
wurde. Die Test-Fixture hielt einen Flask-Kontext über alle Anfragen offen;
Flask-Login merkte sich den Benutzer darin. Der Test prüfte also gar nicht das
Cookie — er wäre auch mit einer kaputten Sitzung grün geblieben.

**Was wir daraus gemacht haben:** Fixture so umgebaut, dass jede Anfrage wie
im echten Betrieb einen eigenen Kontext hat. Zur Gegenprobe `load_user`
absichtlich kaputt gemacht: Jetzt schlägt der Test fehl, wie er soll.
Dieselbe Gegenprobe haben wir später für die Prüfungen von JavaScript und
Vue-Template gemacht.

**Merksatz:** Ein grüner Test beweist nur, dass er nicht fehlschlägt — nicht,
dass er das Richtige prüft. Coverage zeigt, welcher Code nie lief; ein
absichtlich eingebauter Fehler zeigt, ob der Test ihn bemerkt.
