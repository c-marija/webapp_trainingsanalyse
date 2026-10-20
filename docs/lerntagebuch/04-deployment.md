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

<!-- Erster Eintrag hier. Vorlage aus README.md kopieren. -->
