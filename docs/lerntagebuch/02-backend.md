# Backend

Erkenntnisse zu Python, Webframework, Routing, Geschäftslogik und Datenhaltung.
Eintragsformat siehe [README.md](README.md).

Typische Fragen, die hier beantwortet werden sollten:

 * Warum dieses Webframework und nicht ein anderes?
 * Wie ist der Weg einer Anfrage vom Browser bis zur Antwort?
 * Wo liegt die Geschäftslogik, und warum nicht im Frontend?
 * Wie und wo werden Daten gespeichert?
 * Wie validieren wir Eingaben, und warum reicht eine Prüfung im Browser nicht?

---

### 2026-10-20 — Grundgerüst und Datenmodell (SG)

**Ausgangslage:** Bevor die vier Features parallel entstehen können, braucht
es eine gemeinsame Basis: die Flask-Anwendung, das Datenmodell und einen Weg,
die Datenbank mit Demo-Konten und Rückfragen zu füllen.

**Was wir gelernt haben:** Drei Dinge. Erstens: SQLite prüft Fremdschlüssel
standardmässig nicht. Ein Lauf mit einem nicht existierenden Konto würde
lokal gespeichert und erst auf PostgreSQL abgewiesen. Man muss die Prüfung bei
jeder Verbindung ausdrücklich einschalten. Zweitens: Flask sucht seinen
Instanz-Ordner relativ zum Paket — die Datenbankdatei landete zuerst
unbemerkt in `src/instance/`. Drittens: Wo vier Personen dieselbe Zeile
ändern müssten (die Registrierung der Blueprints), entstehen sicher
Merge-Konflikte. Deshalb sind alle vier Blueprints schon im Grundgerüst
registriert.

**Was wir daraus gemacht haben:** Fremdschlüssel in `models.py`
eingeschaltet und mit einem Test abgesichert; Instanz-Ordner ausdrücklich
ins Projektverzeichnis gelegt. Die Entscheide zum Datenmodell stehen in
[0003-datenmodell.md](../decisions/0003-datenmodell.md).

**Offen geblieben:** Für PostgreSQL auf Render fehlen noch ein
Datenbanktreiber und die Umschreibung der Adresse von `postgres://` auf
`postgresql://`.

**Merksatz:** Eine Datenbank ist nur so streng, wie man sie konfiguriert.
Gleiche Technik heisst nicht gleiches Verhalten — darum lokal so nah wie
möglich an der Produktion arbeiten.

---

### 2026-10-20 — Echte Daten sind anders als gedacht (Team)

**Ausgangslage:** Für den CSV-Import haben wir einen echten Garmin-Export als
Grundlage genommen, statt uns auf den Prototyp zu verlassen.

**Was wir gelernt haben:** Der Prototyp prüfte auf den Aktivitätstyp
`Trail Run`, Garmin schreibt aber `Trailrunning`. Mit der alten Regel wären
5 von 39 Läufen — rund 108 km — stillschweigend verloren gegangen, ohne
Fehlermeldung. Dazu kamen Formate, die niemand erwartet hätte: `3,727` heisst
3727 (Komma als Tausendertrennzeichen), `'-5` heisst −5, `--` steht für
„kein Wert", und im selben Export gibt es `true`/`false` *und* `Ja`/`Nein`.

**Was wir daraus gemacht haben:** Alle 34 Spalten mit echten Beispielwerten in
FA-I3 festgehalten; der Parser (`garmin.py`) ist ohne Datenbank testbar. Die
Testdatei enthält erfundene Läufe im exakten Format des echten Exports — die
echten Daten mit Puls und Orten gehören nicht in ein öffentliches Repository.

**Merksatz:** Anforderungen an einen Import schreibt man mit einer echten
Datei vor sich, nicht aus der Erinnerung. Die gefährlichsten Fehler sind die,
bei denen Daten ohne Meldung verschwinden.

---

### 2026-10-20 — Ein KI-Aufruf ist nur HTTP mit JSON (Team)

**Ausgangslage:** Die Trainingsempfehlungen kommen von Gemini. Für Gemini gibt
es eine offizielle Python-Bibliothek, die wäre aber eine neue Dependency
gewesen.

**Was wir gelernt haben:** Ein Aufruf eines Sprachmodells ist im Kern eine
gewöhnliche HTTP-Anfrage: JSON mit dem Prompt hin, JSON mit der Antwort
zurück. Mit `urllib` aus der Standardbibliothek sind das rund 30 Zeilen. Der
API-Schlüssel gehört in den Header, nicht in die URL, weil URLs leicht in
Protokolldateien landen. Und: Der erste echte Testaufruf scheiterte mit „nicht
erreichbar" — tatsächlich brauchte `gemini-3.8-flash` **97 Sekunden** für ein
einziges Wort, unser Programm wartete nur 30.

**Was wir daraus gemacht haben:** Wartezeit auf 150 Sekunden erhöht und die
Wartezeit bewusst akzeptiert (NFA-6 verlangt nur sichtbaren Fortschritt). Alle
Tests laufen gegen eine Attrappe des KI-Service, nie gegen die echte API.

**Offen geblieben:** Gunicorn bricht Anfragen standardmässig nach 30 Sekunden
ab — beim Einrichten von Render braucht der Startbefehl `--timeout 180`.

**Merksatz:** „Nicht erreichbar" kann auch „zu ungeduldig" heissen. Erst die
genaue Fehlerursache (hier eine Zeitüberschreitung) zeigt, wo man ansetzen
muss.

---

### 2026-10-20 — Zeitzonen zwischen Laptop und Server (Team)

**Ausgangslage:** Empfehlungen werden mit Zeitpunkt gespeichert und angezeigt.

**Was wir gelernt haben:** `datetime.now()` liefert die Zeit des Rechners, auf
dem der Code läuft — auf unseren Laptops Schweizer Zeit, auf einem Server in
der Regel UTC. Die Anzeige wäre produktiv je nach Jahreszeit um eine oder zwei
Stunden falsch gewesen, ohne dass es lokal aufgefallen wäre.

**Was wir daraus gemacht haben:** Zeitpunkte in UTC speichern und in der API
mit `Z` kennzeichnen; der Browser rechnet in die lokale Zeit um.

**Merksatz:** Speichern in UTC, anzeigen in Ortszeit. Was lokal stimmt, muss
auf dem Server nicht stimmen.
