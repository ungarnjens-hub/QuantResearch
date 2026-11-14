# R4 Forschungsprotokoll - Explorative Untersuchung
Datum: 2026-11-14
Status: Phase B, zur fachlichen Freigabe

## Hypothese
Vergangene BTC-Renditen enthalten zusätzliche
Prognoseinformation über die nächste ETH-5m-Rendite.

## Daten
Binance USD-M Futures, BTC/ETH, 5m, UTC.
Vorhandene historische Daten, kein Blindtest.
Originaldaten ausschließlich lesend.

## Modelle
B0: Nullrendite.
B1: OLS mit Intercept und ETH-Renditen t,t-1,t-2.
M1: B1 plus BTC-Renditen t,t-1,t-2.
Ziel: ETH-Logrendite Close(t) bis Close(t+1).
Signal nach vollständig abgeschlossener Kerze t.
Keine Parametersuche.

## Zeitliche Validierung
Trainingsbeginn 2024-09-01 UTC.
Monatliche Walk-Forward-Evaluation:
2025-03-01 bis 2026-07-01 exklusiv.
Expanding Training, monatliche Neuschätzung.
Trainingslabels müssen vor Evaluationsbeginn
vollständig bekannt sein.
Training und Evaluation strikt getrennt.

## Primärer Vergleich
MSE(B1) minus MSE(M1).
Zusätzlich relative MSE-Verbesserung.
Gemeinsame Prognosezeitpunkte.
95%-Unsicherheitsintervall mittels
Kalenderwochen-Blockbootstrap,
2000 Wiederholungen, Seed 20261114.
Die Wochenblock-Annahme und Stabilität
sind als Einschränkungen zu dokumentieren.

## Sekundäre Prüfung
Clark-West-adjustierter Prognosevergleich,
HAC-Lag 12, einseitig.
Nur bei erfüllten Voraussetzungen interpretieren.
Keine Auswahl des günstigeren Testergebnisses.

## Entscheidung
Positive Punktschätzung allein reicht nicht.
Positive Differenz mit 95%-Intervall oberhalb
null: explorative Evidenz.
Andernfalls: nicht gestützt oder unklar,
abhängig von Effektgröße und Präzision.
Kein bestätigter unabhängiger Effekt.
Kein Nachweis wirtschaftlicher Profitabilität.

## Stoppregeln
Keine Modell- oder Parameteränderungen nach
Ergebniseinsicht.
Technische oder zeitliche Fehler: Lauf stoppen.
Alle Resultate einschließlich Nullbefunde berichten.
Frühere Versuche und Einschränkungen dokumentieren.

## Schutz
Keine Änderungen an TradingLab, Freqtrade,
Paper-Bots, Originaldaten oder Evidence.
