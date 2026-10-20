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
