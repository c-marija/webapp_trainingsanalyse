# Git und Zusammenarbeit im Team

Erkenntnisse zu Versionskontrolle, Branching-Strategie und der Zusammenarbeit
zu viert. Eintragsformat siehe [README.md](README.md).

---

### 2026-10-20 — Git synchronisiert nicht automatisch (SG)

**Ausgangslage:** Wir arbeiten neu zu viert an einem gemeinsamen Repository auf
GitHub (`c-marija/webapp_trainingsanalyse`). Die Annahme im Team war, dass
Änderungen einer Person automatisch in der VS-Code-Ansicht der anderen
auftauchen — so wie man es von OneDrive oder Google Docs kennt.

**Was wir gelernt haben:** Das stimmt nicht. Git ist ein *verteiltes* System mit
drei getrennten Zuständen, zwischen denen man Änderungen aktiv bewegen muss:

 1. Arbeitsverzeichnis (die Dateien, die ich gerade bearbeite)
 2. Lokales Repository (`.git`-Ordner auf meinem Rechner) — erreicht durch
    `git add` und `git commit`
 3. Remote-Repository auf GitHub (`origin`) — erreicht durch `git push`

Umgekehrt kommt fremde Arbeit erst durch `git pull` zu mir. Nichts davon
passiert von selbst. Der Vorteil dieser Trennung: Man kann offline arbeiten,
Zwischenstände committen, ohne sie zu veröffentlichen, und die Historie bleibt
nachvollziehbar.

**Was wir daraus gemacht haben:** Feste Routine im Team vereinbart — `git pull`
vor Arbeitsbeginn, `git commit` und `git push` am Ende jeder Arbeitseinheit. In
VS Code haben wir `git.autofetch` aktiviert, damit die Statusleiste unten links
anzeigt, wie viele Commits auf GitHub bereitliegen (`↓`) und wie viele eigene
noch nicht gepusht sind (`↑`).

**Offen geblieben:** Ob wir direkt auf `master` arbeiten oder pro Aufgabe einen
Feature-Branch mit Pull Request anlegen. *Nachtrag 2026-10-20:* Entschieden
für Feature-Branches mit Pull Request, siehe
[0002-branching-und-zusammenarbeit.md](../decisions/0002-branching-und-zusammenarbeit.md).

**Merksatz:** Git ist pull-basiert, nicht push-basiert aus Sicht des Empfängers.
Änderungen anderer erreichen meinen Rechner ausschliesslich dann, wenn ich sie
mit `git pull` hole.

---

### 2026-10-20 — Merge-Konflikte sind ein Normalzustand, kein Fehler (SG)

**Ausgangslage:** Unsicherheit im Team, was passiert, wenn zwei Personen
gleichzeitig an derselben Datei arbeiten.

**Was wir gelernt haben:** Git unterscheidet drei Fälle. Verschiedene Dateien
und verschiedene Stellen derselben Datei führt Git selbstständig zusammen. Nur
wenn zwei Personen **dieselben Zeilen** geändert haben, entsteht ein
Merge-Konflikt: Git markiert die Stelle mit `<<<<<<<`, `=======` und `>>>>>>>`
und überlässt uns die Entscheidung. Das ist bewusst so — Git kann inhaltlich
nicht wissen, welche Version richtig ist.

**Was wir daraus gemacht haben:** Zwei Massnahmen, um Konflikte seltener zu
machen: kleine und häufige Commits statt grosser Sammel-Commits, und eine klare
Aufgabenteilung, sodass möglichst nicht zwei Personen gleichzeitig am selben
Modul arbeiten.

**Merksatz:** Ein Merge-Konflikt bedeutet nicht, dass etwas kaputt ist. Er
bedeutet, dass Git eine inhaltliche Entscheidung nicht treffen kann und sie an
uns zurückgibt.

---

### 2026-10-20 — Pull Requests und Freigaben im Team (Team)

**Ausgangslage:** Seit ADR 0002 gelangt jede Änderung nur über einen Pull
Request nach `master`. Heute haben wir sechs Pull Requests geprüft und
gemergt.

**Was wir gelernt haben:** Die Zusammenarbeit mit Freigabe (Approve) durch
eine zweite Person hat funktioniert. Drei Details haben wir unterwegs
gelernt:

 * **Comment ist nicht Approve.** Bei einem Review gibt es drei Varianten.
   Nur *Approve* dokumentiert auf GitHub, dass jemand den Code geprüft und für
   gut befunden hat. Und: Erst freigeben, dann mergen.
 * **Den eigenen Pull Request kann man nicht freigeben.** Wer ihn geöffnet
   hat, braucht eine zweite Person.
 * **Aufeinander aufbauende Pull Requests** (#4 → #5 → #6) müssen in dieser
   Reihenfolge und mit „Create a merge commit" gemergt werden. Solange der
   erste offen ist, zeigt der zweite dessen Commits mit an; nach dem Merge
   verschwinden sie automatisch.

**Was wir daraus gemacht haben:** Jeder Pull Request enthält eine Prüfliste
für den Browser. Eine Person testet, gibt frei und mergt; danach holen alle
mit `git pull` den neuen Stand.

**Offen geblieben:** Ob wir die Freigabe über eine Branch-Schutzregel auf
GitHub erzwingen (offener Punkt in ADR 0002).

**Merksatz:** Der Pull Request ist der einzige Kontrollpunkt zwischen „fertig
auf meinem Rechner" und „für alle sichtbar" — und sobald Render läuft, auch
„öffentlich deployt".

---

### 2026-11-03 — Branch-Schutz: zu streng ist auch falsch (Team)

**Ausgangslage:** Nach dem ersten Deployment haben wir auf GitHub ein
Ruleset für `master` eingerichtet, damit jeder Pull Request von einer zweiten
Person freigegeben werden muss. Danach liess sich Pull Request #10 nicht
mergen, obwohl er freigegeben war.

**Was wir gelernt haben:** GitHub zeigte `APPROVED` und trotzdem
`BLOCKED`. Genau dieser Widerspruch führte zur Ursache: Im Ruleset waren
neben den drei gewollten Regeln auch „Restrict creations" und „Restrict
updates" angekreuzt. „Restrict updates" heisst, dass **niemand** `master`
verändern darf — auch nicht über einen freigegebenen Pull Request. Damit war
der Hauptbranch eingefroren. Schutzregeln sind Verbote: Jedes zusätzliche
Häkchen schränkt mehr ein, nicht weniger.

**Was wir daraus gemacht haben:** Die zwei Häkchen entfernt. Für `master`
gelten jetzt genau drei Regeln: Pull Request mit einer Freigabe, kein
Force-Push, kein Löschen. Festgehalten im Nachtrag zu
[0002-branching-und-zusammenarbeit.md](../decisions/0002-branching-und-zusammenarbeit.md).
Nebenbei: Dass GitHub die Änderungen an `index.html` nicht anzeigen konnte,
war ein anderes, harmloses Problem — der Diff enthielt die gelöschte
Vue-Kopie mit rund 190 KB in wenigen sehr langen Zeilen.

**Merksatz:** Bei Sicherheitseinstellungen nur ankreuzen, was man erklären
kann. Wenn zwei Statusangaben sich widersprechen („freigegeben" und
„blockiert"), liegt die Ursache meist in einer Regel, die man nicht bewusst
gesetzt hat.

---

### 2026-11-03 — Gemergt heisst nicht deployt (Team)

**Ausgangslage:** Pull Request #10 entfernte das Abzeichen „BEISPIEL". Nach
dem Merge stand es auf der öffentlichen Seite trotzdem noch da.

**Was wir gelernt haben:** Am Browser-Cache lag es nicht: Die Seite lieferte
tatsächlich noch die alte Version aus. Bei Render war `f032b49` (#10) gar
nicht deployt worden; live war noch #9, und zwar mit dem Vermerk „by you" —
also von Hand ausgelöst. Auto-Deploy war nicht eingeschaltet. Unsere
Dokumentation (ADR 0002, `AGENTS.md`) ging davon aus, dass jeder Merge auf
`master` sofort live geht. Das stimmte nicht, und niemand hat es bemerkt,
bis eine sichtbare Änderung ausblieb.

**Was wir daraus gemacht haben:** Von Hand nachdeployt („Manual Deploy").
Damit es nicht wieder passiert, muss Auto-Deploy bei Render unter *Settings →
Build & Deploy* auf „On Commit" stehen. Den Live-Stand haben wir danach
direkt geprüft: Die Seite ist von 200 KB auf 31 KB geschrumpft, das Abzeichen ist
weg.

**Merksatz:** Nach einem Merge den Live-Stand prüfen, nicht annehmen. Der
Commit, der bei Render als „Live" angezeigt wird, ist die einzige verlässliche
Antwort auf die Frage, was die Benutzer gerade sehen.
