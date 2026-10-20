# Businessanforderungen PaceMaker

Stand: 2026-10-20 · Grundlage: Prototyp `src/app/static/index.html` und
Architekturübersicht des Teams

## 1. Zweck dieses Dokuments

Dieses Dokument beschreibt, **was** die Anwendung aus fachlicher Sicht leisten
muss — nicht, wie sie technisch umgesetzt wird. Die Technologiewahl steht in
[decisions/0001-technologiewahl.md](decisions/0001-technologiewahl.md).

Die Anforderungen sind so geschnitten, dass sie zum aktuellen Projektstand
passen: Der Frontend-Prototyp ist fertig und definiert das gewünschte
Verhalten. Die Anforderungen beschreiben daher im Kern, **was das Backend
leisten muss, damit der Prototyp mit echten, dauerhaft gespeicherten Daten
funktioniert.**

**Priorisierung**

| Stufe | Bedeutung |
|---|---|
| MUSS | Ohne diese Anforderung ist die Anwendung nicht abgabefähig. |
| SOLL | Deutlicher Mehrwert, wird umgesetzt, sobald alle MUSS erfüllt sind. |
| KANN | Wünschenswert, wird nur bei verbleibender Zeit umgesetzt. |

## 2. Ausgangslage und Geschäftsziel

Freizeitläuferinnen und Freizeitläufer sammeln mit Uhren wie Garmin über Jahre
Trainingsdaten. Diese Daten liegen jedoch als unstrukturierte Liste vor und
beantworten die Fragen nicht, die beim Training tatsächlich auftauchen:
*Steigere ich zu schnell? Ist meine Zielzeit realistisch? Was soll ich diese
Woche laufen?*

PaceMaker führt die eigenen Trainingsdaten mit dem persönlichen Ziel zusammen
und lässt daraus verständliche Trainingsempfehlungen in natürlicher Sprache
erzeugen.

**Geschäftsziel:** Eine Läuferin kann ihre bestehenden Trainingsdaten in
weniger als fünf Minuten importieren und erhält anschliessend eine
nachvollziehbare, auf ihre Daten bezogene Antwort auf eine Trainingsfrage.

## 3. Rollen

| Rolle | Beschreibung |
|---|---|
| **Gast** | Nicht angemeldet. Sieht ausschliesslich Anmeldung und Registrierung. |
| **Läuferin / Läufer** | Angemeldet. Einzige fachliche Rolle. Sieht und bearbeitet ausschliesslich die eigenen Daten. |

Es gibt bewusst **keine Administrationsrolle**. Eine solche würde zusätzliche
Oberflächen und Rechteprüfungen erfordern, ohne zum Lernziel beizutragen.

## 4. Begriffe

| Begriff | Bedeutung |
|---|---|
| **Lauf** | Eine einzelne Trainingseinheit mit Startzeitpunkt, Distanz und Bewegungszeit. |
| **Bewegungszeit** | Reine Laufzeit ohne Pausen. Grundlage aller Tempoberechnungen. |
| **Tempo (Pace)** | Bewegungszeit geteilt durch Distanz, angegeben als mm:ss pro Kilometer. |
| **Wochenumfang** | Summe der Kilometer innerhalb einer Kalenderwoche. |
| **Rückfragen** | Vier Fragen zu Ziel, Trainingshäufigkeit, aktuellem Umfang und Einschränkungen. |
| **Empfehlung** | Vom Sprachmodell erzeugte Antwort auf eine ausgewählte Trainingsfrage. |

---

## 5. Funktionale Anforderungen

### 5.1 Konto und Anmeldung

**FA-A1 — Registrierung · MUSS**
Für den Scope der Arbeit soll es noch kein Registrierungsfeature geben. Wir möchten 2 Demouser haben, welcher direkt in den datenbanken hinterlegt ist.

*Akzeptanzkriterien*
 * ein Testuser ist vorhanden

**FA-A2 — Anmeldung · MUSS**
Eine registrierte Person meldet sich mit E-Mail-Adresse und Passwort an.

*Akzeptanzkriterien*
 * Bei unbekannter E-Mail-Adresse **und** bei falschem Passwort erscheint
   dieselbe Meldung („E-Mail oder Passwort ist falsch"). Unterschiedliche
   Meldungen würden verraten, welche Adressen registriert sind.
 * Die Anmeldung bleibt über mehrere Seitenaufrufe hinweg bestehen.

**FA-A3 — Abmeldung · MUSS**
Eine angemeldete Person kann sich abmelden; die Sitzung wird serverseitig
beendet.

**FA-A4 — Sitzung prüfen · MUSS**
Die Anwendung kann feststellen, wer angemeldet ist, und zeigt den Namen an.
Ohne gültige Sitzung wird die Anmeldemaske angezeigt.

**FA-A5 — Datentrennung zwischen Konten · MUSS**
Jede Person sieht und verändert ausschliesslich ihre eigenen Läufe,
Rückfragen und Empfehlungen.

*Akzeptanzkriterien*
 * Jeder Zugriff auf einen Datensatz prüft serverseitig, ob er zum angemeldeten
   Konto gehört.
 * Der Versuch, über eine fremde Datensatz-Nummer zuzugreifen, wird abgewiesen.
   Es genügt **nicht**, fremde Daten nur in der Oberfläche auszublenden.



### 5.2 Import aus Garmin Connect

**FA-I1 — CSV-Datei hochladen · MUSS**
Eine angemeldete Person lädt die Datei `Activities.csv` aus Garmin Connect
hoch; die enthaltenen Läufe werden ihrem Konto zugeordnet gespeichert.

*Akzeptanzkriterien*
 * Auswahl über einen Dateidialog **und** über Ziehen-und-Fallenlassen.
 * Die Datei wird **auf dem Server** ausgewertet, nicht im Browser.

**FA-I2 — Nur Läufe übernehmen · MUSS**
Aus dem Export werden ausschliesslich Aktivitäten der Typen `Laufen`,
`Laufbandtraining` und `Trailrunning` übernommen. Radfahren, Schwimmen und
Kraftraining werden übersprungen.

*Akzeptanzkriterien*
 * Die Typbezeichnungen stimmen exakt mit dem Garmin-Export überein. Der
   Prototyp prüft auf `Trail Run` und würde damit alle Trailläufe verwerfen.
 * `Laufbandtraining` kommt im vorliegenden Beispielexport nicht vor. Die
   Bezeichnung ist vor der Umsetzung an einem Export mit Laufbandläufen zu
   prüfen.

**FA-I3 — Je Lauf übernommene Angaben · MUSS**
Alle 34 Spalten des Garmin-Exports werden übernommen und je Lauf gespeichert.
Grundlage ist ein echter Export aus Garmin Connect mit deutscher
Spracheinstellung und metrischen Einheiten. Der Export selbst enthält keine
Einheiten; die Einheiten unten sind aus den Werten abgeleitet.

Pflicht sind nur die mit *ja* markierten Spalten. Fehlt eine Pflichtangabe,
wird die Zeile übersprungen und als fehlerhaft gezählt — der Import als Ganzes
bricht nicht ab. Fehlt eine optionale Angabe oder steht dort `--`, bleibt das
Feld leer.

*Grunddaten*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Aktivitätstyp | Art der Aktivität | Text, siehe FA-I2 | ja | `Laufen` |
| Datum | Startzeitpunkt, Ortszeit | JJJJ-MM-TT hh:mm:ss | ja | `2026-09-30 18:38:25` |
| Titel | Bezeichnung des Laufs | Text | nein, Vorgabe „Lauf" | `Luzern - Basis` |
| Favorit | in Garmin als Favorit markiert | `true` / `false` | nein | `false` |
| Distanz | Länge des Laufs | km | ja | `7.06` |
| Kalorien | Energieverbrauch | kcal | nein | `3,727` |

*Zeiten*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Zeit in Bewegung | reine Laufzeit ohne Stillstand | h:mm:ss | ja, ersatzweise `Zeit` | `00:57:18` |
| Zeit | Timerzeit der Uhr | h:mm:ss | nein | `00:57:21` |
| Verstrichene Zeit | Start bis Ende inkl. Pausen | h:mm:ss | nein | `00:57:26` |
| Anzahl der Runden | Runden laut Uhr | ganze Zahl | nein | `19` |
| Beste Rundenzeit | schnellste Runde | h:mm:ss mit Zehntelsekunden | nein | `00:00:06.2` |

*Tempo*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Ø Pace | Durchschnittstempo laut Garmin | mm:ss pro km | nein | `8:08` |
| Beste Pace | schnellstes Tempo | mm:ss pro km | nein | `4:08` |
| Durchschnittliche SAP | steigungsbereinigtes Tempo | mm:ss pro km | nein | `7:58` |

*Herzfrequenz und Belastung*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Ø Herzfrequenz | durchschnittlicher Puls | Schläge/min | nein | `127` |
| Maximale Herzfrequenz | höchster Puls | Schläge/min | nein | `153` |
| Aerober TE | aerober Trainingseffekt | 0,0 bis 5,0 | nein | `2.2` |
| Training Stress Score® | Trainingsbelastung | Dezimalzahl | nein | `0.0` |
| Body Battery Abnahme | Energieverbrauch laut Uhr | ganze Zahl, negativ | nein | `'-5` |

*Höhe*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Anstieg gesamt | Höhenmeter bergauf | m | nein | `1,993` |
| Abstieg gesamt | Höhenmeter bergab | m | nein | `237` |
| Minimale Höhe | tiefster Punkt | m ü. M. | nein | `425` |
| Maximale Höhe | höchster Punkt | m ü. M. | nein | `2,326` |

*Laufdynamik*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Ø Schrittfrequenz (Laufen) | Schritte pro Minute | Schritte/min | nein | `148` |
| Max. Schrittfrequenz (Laufen) | höchste Schrittfrequenz | Schritte/min | nein | `191` |
| Ø Schrittlänge | durchschnittliche Schrittlänge | m | nein | `0.84` |
| Durchschnittliches vertikales Verhältnis | vertikale Bewegung im Verhältnis zur Schrittlänge | % | nein | `10.2` |
| Ø vertikale Bewegung | Auf- und Abbewegung des Körpers | cm | nein | `8.2` |
| Ø Bodenkontaktzeit | Dauer des Bodenkontakts je Schritt | ms | nein | `307` |
| Schritte | Gesamtzahl Schritte | Anzahl | nein | `8,422` |

*Leistung*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Ø Leistung | durchschnittliche Laufleistung | Watt | nein | `217` |
| Max. Leistung | höchste Laufleistung | Watt | nein | `449` |
| Normalized Power® (NP®) | belastungsgewichtete Leistung | Watt | nein | `227` |

*Sonstiges*

| Spalte im Export | Bedeutung | Format, Einheit | Pflicht | Beispiel |
|---|---|---|---|---|
| Dekompression | Tauchfunktion, bei Läufen stets „Nein" | `Ja` / `Nein` | nein | `Nein` |

Zusätzlich zu den Exportspalten wird je Lauf die Quelle (`garmin_csv`) und die
Zuordnung zum Konto gespeichert.

*Akzeptanzkriterien*
 * Jede der 34 Spalten hat ein eigenes Feld; keine Spalte wird verworfen.
 * Zahlen werden als Zahlen gespeichert, Zeiten und Tempi in Sekunden,
   Wahrheitswerte als Wahrheitswert — nicht als Text. Nur so lassen sich
   später Durchschnitte bilden und Werte sortieren.
 * Im Logbuch werden weiterhin nur die Angaben aus FA-L1 angezeigt. Die
   übrigen Felder bleiben gespeichert und stehen für Empfehlungen (5.5) und
   spätere Erweiterungen zur Verfügung.

*Hinweis zum Tempo:* Garmins `Ø Pace` beruht auf `Zeit`, das im Logbuch
angezeigte Tempo (FA-L1) auf `Zeit in Bewegung`. Bei Läufen mit Pausen
weichen die Werte voneinander ab — beim Lauf Interlaken–Lauterbrunnen etwa
7:24 laut Garmin gegenüber 7:21 berechnet. Beide werden gespeichert;
massgeblich für Anzeige und Empfehlungen bleibt das berechnete Tempo.

*Datenmodell vom Decision File übernehmen, falls nicht vorhanden, erstellen.*

**FA-I4 — Duplikate überspringen · MUSS**
Ein Lauf gilt als bereits vorhanden, wenn die folgenden Angaben bereits in einem gespeicherten Lauf enthalten sind:
| Aktivitätstyp | Art der Aktivität | Text, siehe FA-I2 | ja | `Laufen` |
| Datum | Startzeitpunkt, Ortszeit | JJJJ-MM-TT hh:mm:ss | ja | `2026-09-30 18:38:25` |
Der doppelte Datensatz soll übersprungen werden. Der gesamte Import darf nicht abgebrochen werden.

*Begründung:* Garmin-Exporte überschneiden sich zeitlich. Ohne diese Regel
entstehen bei jedem Import Doppeleinträge, die alle Auswertungen verfälschen.

**FA-I5 — Rückmeldung zum Import · MUSS**
Nach dem Import erscheint eine Zusammenfassung mit vier Zahlen: importiert,
Duplikate übersprungen, keine Läufe, fehlerhafte Zeilen.

**FA-I6 — Falsche Datei erkennen · MUSS**
Fehlen die Spalten `Aktivitätstyp` oder `Datum`, wird die Datei mit einer
verständlichen Meldung abgewiesen, statt einen technischen Fehler zu zeigen.

**FA-I7 — Robuste Zahlen- und Zeitformate · MUSS**
Der Import verarbeitet die Eigenheiten des Garmin-Exports:

 * Komma als Tausendertrennzeichen, Punkt als Dezimaltrennzeichen:
   `3,727` bedeutet 3727, `7.06` bedeutet 7,06
 * Apostroph vor negativen Zahlen: `'-5` bedeutet −5
 * `--` als Platzhalter für fehlende Werte
 * Zeiten als `hh:mm:ss`, mit oder ohne Zehntelsekunden (`00:03:44.6`)
 * Tempi als `mm:ss`
 * zwei Schreibweisen für Wahrheitswerte im selben Export: `true`/`false`
   und `Ja`/`Nein`
 * Spaltennamen mit Umlauten und Sonderzeichen (`Ø`, `®`), Zeichenkodierung
   UTF-8, gegebenenfalls mit Byte-Reihenfolge-Markierung am Dateianfang

*Begründung:* Das ist in der Praxis der fehleranfälligste Teil des Imports.

**FA-I8 — Unterstützte Exportvariante · MUSS**
Unterstützt wird der Export aus Garmin Connect mit deutscher
Spracheinstellung und metrischen Einheiten.

*Akzeptanzkriterien*
 * Ein Export in anderer Sprache wird an den fehlenden deutschen Spaltennamen
   erkannt und nach FA-I6 abgewiesen.
 * Der Hinweistext beim Import nennt diese Voraussetzung.

*Begründung:* Spaltennamen und Einheiten hängen von den Kontoeinstellungen in
Garmin Connect ab. Ein Export mit Meilen und Fuss lässt sich an den Werten
nicht zuverlässig erkennen und würde unbemerkt falsche Distanzen liefern.

### 5.3 Logbuch

**FA-L1 — Läufe anzeigen · MUSS**
Das Logbuch listet alle Läufe des Kontos mit Datum, Uhrzeit, Titel, Distanz,
Bewegungszeit, Tempo, Ø Puls und Höhenmetern.

*Akzeptanzkriterien*
 * Das Tempo wird aus Bewegungszeit und Distanz berechnet, nicht gespeichert.
 * Fehlende optionale Werte erscheinen als „–", nicht als leere Zelle oder `null`.
 * Läufe auf dem Laufband sind als solche erkennbar.

**FA-L2 — Sortieren · MUSS**
Die Liste lässt sich nach Datum, Distanz, Zeit, Tempo, Puls und Höhenmetern
auf- und absteigend sortieren. Voreinstellung: Datum, neueste zuerst.

**FA-L3 — Zusammenfassung · MUSS**
Über der Liste stehen Anzahl Läufe und Gesamtkilometer. Der Zeitraum in welchem die Läufe stattgefunden haben werden ebenfalls angezeigt. 

**FA-L4 — Lauf manuell erfassen · MUSS**
Ein Lauf lässt sich ohne Import eintragen: Datum und Uhrzeit, Titel, Distanz,
Zeit und optional Ø Puls.

*Akzeptanzkriterien*
 * Zeiteingabe als `h:mm:ss` oder `mm:ss`.
 * Distanz zwischen 0,5 und 100 km, Puls zwischen 60 und 220.
 * Diese Grenzen werden **serverseitig** geprüft. Die Prüfung im Browser ist
   Bedienkomfort und ersetzt sie nicht.
 * Der Lauf wird mit Quelle `manuell` gespeichert.
 * Alle weiteren Angaben aus FA-I3 bleiben bei manuell erfassten Läufen leer.

**FA-L5 — Lauf löschen · MUSS**
Ein einzelner Lauf lässt sich entfernen. Gelöscht wird nur, wenn der Lauf zum
angemeldeten Konto gehört.

**FA-L6 — Leerer Zustand · MUSS**
Ohne Läufe erscheint ein Hinweis, der auf Import und manuelle Erfassung
verweist — keine leere Tabelle.

**FA-L7 — Schweizer Darstellung · SOLL**
Datum als TT.MM.JJJJ, Zeiten als h:mm:ss, Distanzen mit zwei Nachkommastellen,
Zahlen in Tabellen mit gleicher Ziffernbreite.

### 5.4 Ziele und Rückfragen

**FA-Z1 — Vier Rückfragen beantworten · MUSS**
Eine angemeldete Person beantwortet vier Fragen. Sie bilden den
Anfangsbestand in der Datenbank (FA-Z5):

 1. **Trainingsziel** — Auswahl aus: Wettkampf, schneller werden, mehr Umfang,
    fit bleiben
 2. **Einheiten pro Woche** — Auswahl von 1 bis 7
 3. **Aktueller Wochenumfang** — Zahl in Kilometern (0 bis 250)
 4. **Einschränkungen** — Freitext, höchstens 200 Zeichen, optional

**FA-Z2 — Wettkampf erfassen · MUSS**
Bei Ziel *Wettkampf* werden zusätzlich erfasst: Name, Datum, Distanz (5 km,
10 km, Halbmarathon 21,0975 km, Marathon 42,195 km) und Zielzeit.

*Akzeptanzkriterien*
 * Diese Felder erscheinen nur bei Ziel *Wettkampf*.
 * Wechselt das Ziel auf einen anderen Wert, wird der Wettkampf nicht mehr
   als aktiv geführt.

**FA-Z3 — Vorschlag für den Wochenumfang · MUSS**
Beim Öffnen der Rückfragen wird aus den gespeicherten Läufen der
Durchschnitt der letzten vier Wochen berechnet und als Orientierung angezeigt.

*Begründung:* Die wenigsten Menschen kennen ihren Wochenumfang auswendig. Der
Vorschlag macht aus einer Schätzung eine belastbare Angabe.

**FA-Z4 — Antworten speichern · MUSS**
Die Antworten werden dauerhaft gespeichert, beim nächsten Besuch vorbelegt und
sind jederzeit änderbar. Das Speichern wird sichtbar bestätigt.

**FA-Z5 — Fragen und Antwortoptionen aus der Datenbank · MUSS**
Die Rückfragen und ihre Antwortoptionen sind in der Datenbank hinterlegt,
nicht im Programmcode. Die vier Fragen aus FA-Z1 bilden den Anfangsbestand.

*Akzeptanzkriterien*
 * Die Oberfläche baut das Formular aus den Fragen und Optionen auf, die das
   Backend liefert. Weder Fragetexte noch Optionen stehen fest im Frontend.
 * Jede Frage hat eine Reihenfolge und einen Antworttyp: *Auswahl*, *Zahl*
   oder *Freitext*. Nur Auswahlfragen haben Antwortoptionen.
 * Eine in der Datenbank geänderte Frage oder Option erscheint ohne
   Codeänderung.
 * Der Anfangsbestand wird beim Einrichten der Datenbank automatisch angelegt,
   damit lokal und produktiv dieselben Fragen gelten.
 * Gespeicherte Antworten (FA-Z4) verweisen auf ihre Frage und bei
   Auswahlfragen auf die gewählte Option.
 * Die Wettkampfangaben aus FA-Z2 sind keine Rückfrage. Sie erscheinen, wenn
   bei der Zielfrage die Option *Wettkampf* gewählt ist.

*Begründung:* Entspricht den Tabellen `goal_questions` und `goal_options` der
Architekturübersicht. Entscheid des Teams vom 2026-10-20.

### 5.5 Trainingsempfehlungen

**FA-E1 — Fragenauswahl · MUSS**
Zur Auswahl stehen vier vorgegebene Fragen:

 * Wie kann ich mein Training verbessern?
 * Ist mein Ziel mit meinem aktuellen Training realistisch?
 * Steigere ich meinen Umfang zu schnell?
 * Was soll ich diese Woche laufen?

**FA-E2 — Kontext aus den eigenen Daten · MUSS**
Mit der Frage wird ein Datenkontext an das Sprachmodell übergeben:

 * alle Antworten aus den Rückfragen
 * der Wettkampf mit Datum, Distanz und Zielzeit, sofern erfasst
 * alle erfassten Läufe mit Datum, Distanz, Dauer, Tempo, Ø Puls,
   Höhenmetern und Laufband-Kennzeichen


*Akzeptanzkriterien*
 * Der Kontext wird **serverseitig** aus der Datenbank aufgebaut.
 * Er enthält **keine** Namen, E-Mail-Adressen oder Kontonummern. Die
   übermittelten Daten sind damit nicht unmittelbar einer Person zuzuordnen.

**FA-E3 — Antwort anzeigen · MUSS**
Die Antwort erscheint als zusammenhängender Text. Während der Verarbeitung ist
erkennbar, dass die Anwendung arbeitet.

**FA-E4 — Übermittelte Daten offenlegen · MUSS**
Auf Wunsch zeigt die Anwendung genau den Text, der an das Sprachmodell
geschickt wurde.

*Begründung:* Nachvollziehbarkeit ist bei automatisch erzeugten Empfehlungen
zentral. Ohne diese Offenlegung ist für niemanden prüfbar, worauf eine
Empfehlung beruht.

**FA-E5 — Störungen des Sprachmodells abfangen · MUSS**
Ist der Dienst nicht erreichbar, das Kontingent erschöpft oder die Antwort
leer, erscheint eine verständliche Meldung. Die übrige Anwendung bleibt
benutzbar.

*Begründung:* Das Kontingent ist kostenlos und damit begrenzt. Ein Ausfall
während der Prüfungspräsentation darf nicht die ganze Anwendung lahmlegen.

**FA-E6 — Nur die letzte Empfehlung aufbewahren · MUSS**
Je Konto wird ausschliesslich die zuletzt erzeugte Empfehlung aufbewahrt, mit
Frage, Antwort, Zeitpunkt und übermitteltem Kontext. Eine neu erzeugte
Empfehlung überschreibt die vorherige.

*Akzeptanzkriterien*
 * Beim Öffnen der Trainingstipps wird die letzte Empfehlung samt Zeitpunkt
   angezeigt, sofern eine existiert.
 * Es gibt keinen Verlauf früherer Empfehlungen.
 * Schlägt die Erzeugung fehl (FA-E5), bleibt die bisherige Empfehlung
   erhalten.

*Begründung:* Entspricht der Tabelle `recommendations` und dem Endpunkt
`/recommendation` (generieren, abrufen) der Architekturübersicht. Auf einen
Verlauf wurde im Team bewusst verzichtet (Entscheid vom 2026-10-20).

**FA-E7 — Keine Empfehlung ohne Datengrundlage · SOLL**
Sind weder Läufe noch Rückfragen erfasst, weist die Anwendung darauf hin,
statt das Sprachmodell ohne Grundlage zu befragen.


---

## 6. Nicht-funktionale Anforderungen

**NFA-1 — Dauerhaftigkeit · MUSS**
Alle Daten überstehen einen Neustart der Anwendung. Der heutige Zustand des
Prototyps — Daten verschwinden beim Neuladen — ist ausdrücklich nicht
ausreichend.

**NFA-2 — Öffentlich erreichbar · MUSS**
Die Anwendung ist unter einer öffentlichen Adresse über HTTPS erreichbar und
ohne Installation nutzbar.

**NFA-3 — Serverseitige Prüfung · MUSS**
Jede Eingabe wird serverseitig validiert. Jede Prüfung, die nur im Browser
stattfindet, gilt als nicht vorhanden.

**NFA-4 — Keine Geheimnisse im Repository · MUSS**
API-Schlüssel, Datenbankzugänge und der Sitzungsschlüssel stehen in
Umgebungsvariablen. Im Repository liegt lediglich eine Beispieldatei ohne
echte Werte.

**NFA-5 — Verständliche Fehlermeldungen · MUSS**
Fehler erscheinen in verständlicher Sprache an der Stelle, an der sie
entstehen. Technische Fehlerausgaben gelangen nie zur Nutzerin.

**NFA-6 — Antwortzeiten · SOLL**
Logbuch und Rückfragen antworten in unter einer Sekunde. Der Import von 500
Läufen dauert höchstens 10 Sekunden. Für Empfehlungen gilt keine Vorgabe, da
sie von einem fremden Dienst abhängen — der Fortschritt muss aber sichtbar sein.

**NFA-7 — Bedienung auf dem Mobilgerät · SOLL**
Die Anwendung ist ab 360 Pixel Breite bedienbar. Die Logbuchtabelle darf
seitlich scrollen.

**NFA-8 — Barrierefreiheit · SOLL**
Alle Funktionen sind mit der Tastatur erreichbar, Formularfelder sind
beschriftet, die Tabellensortierung ist für Screenreader erkennbar. Der
Prototyp erfüllt das bereits; es darf beim Umbau nicht verloren gehen.

**NFA-9 — Nachvollziehbare Entscheidungen · MUSS**
Architektur- und Technologieentscheidungen sind in `docs/decisions`
dokumentiert, Erkenntnisse im Lerntagebuch festgehalten.

**NFA-10 — Tests der Fachlogik · SOLL**
CSV-Import, Duplikaterkennung, Tempoberechnung und Wochenaggregation sind
durch automatische Tests abgedeckt.

*Begründung:* Genau dort entstehen stille Rechenfehler, die in der Oberfläche
plausibel aussehen.

---

## 7. Nicht Bestandteil dieser Version

Bewusst ausgeschlossen, um den Umfang beherrschbar zu halten:

 * Passwort zurücksetzen und E-Mail-Bestätigung
 * Anmeldung über Google, Garmin oder andere Anbieter
 * Direkte Anbindung an die Garmin-API (nur CSV-Import)
 * Garmin-Exporte in anderen Sprachen oder mit imperialen Einheiten (siehe FA-I8)
 * Konto löschen und Daten exportieren
 * Teilen von Trainings, soziale Funktionen, Vergleich mit anderen
 * Mehrsprachigkeit (die Anwendung ist deutschsprachig)
 * Weitere Sportarten als Laufen
 * Vollständige Trainingspläne über mehrere Wochen
 * Freie Fragen an das Sprachmodell (nur die vier vorgegebenen Fragen)
 * Verlauf früherer Empfehlungen (siehe FA-E6)
 * Diagramme und grafische Auswertungen
 * Administrationsbereich
 * Registrierung, es wird auschliesslich mit den Demousern gearbeitet

