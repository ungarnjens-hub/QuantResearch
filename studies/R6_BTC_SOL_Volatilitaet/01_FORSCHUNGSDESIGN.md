# R6 - Forschungsdesign Version 0.1
Status: Phase A, Entwurf

FRAGE:
Verbessert bekannte BTC-Volatilitaet die
Prognose der naechsten 60 Minuten
SOL-Volatilitaet gegenueber SOL-HAR-RV?

MECHANISMUS:
Marktweite Volatilitaetsschocks koennten
von BTC auf SOL uebertragen werden.
Alternative: Gemeinsame Informationsschocks.

H0:
Keine inkrementelle OOS-Verbesserung.

H1:
Positive inkrementelle OOS-Verbesserung.

VORGESEHENE BASELINES:
Historischer SOL-Volatilitaetsmittelwert,
SOL-HAR-RV ohne BTC.
Kandidat: SOL-HAR-RV plus BTC-RV.

PRIMAERES ZIEL:
Relative OOS-MSE-Verbesserung auf
dem logarithmierten 60m-RV-Ziel.
Gepaarte Unsicherheitsintervalle.

METHODIK:
R5 als feststehende Referenz.
Abweichungen nur vor Messung begruenden.
Chronologisches Walk-Forward.
Keine Parametersuche.
Kein erneuter historischer Blindtest.

PHASE B MUSS PRUEFEN:
- R5-Methodik auf SOL uebertragbar?
- Datenquellen und SOL-Datenhistorie
- Vorherige SOL-Untersuchungen und Dateneinsicht
- Trainingsfenster und gemeinsame Zeitachse
- Zeitliche Verfuegbarkeit von Features/Labels
- Geeignete Inferenz und Entscheidungskriterien
- Verfuegbarkeit neuer Bestaetigungsdaten

STOP:
Keine Ergebnismessung vor Methodenaudit
und ausdruecklicher Freigabe.
Keine Produktivaenderungen.
