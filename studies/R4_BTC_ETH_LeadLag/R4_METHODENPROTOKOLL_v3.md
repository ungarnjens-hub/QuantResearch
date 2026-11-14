# R4 BTC-ETH Lead-Lag | Version 2
Status: Phase B, vor Ergebnismessung
Datum: 2026-11-14

## Hypothese
H0: BTC-Lags liefern keine zusätzliche OOS-Prognosegüte.
H1: BTC-Lags verbessern die ETH-Renditeprognose.

## Population
Binance USD-M Perpetual, BTC und ETH, 5m, UTC.
Alle vorhandenen historischen Daten gelten als
explorativ/voranalysiert, nicht als neuer Blindtest.

## Ziel
ETH-Logrendite von Close(t) bis Close(t+1).
Prognoseentscheidung nach Abschluss von Kerze t.
Empfangslatenz unbekannt; keine Ausführbarkeitsaussage.

## Modelle
B0: Nullrendite.
B1: ETH-AR(3), mit Achsenabschnitt.
M1: B1 plus BTC-Lags 0, 1 und 2,
jeweils zum Prognosezeitpunkt abgeschlossen.
OLS, keine Standardisierung, keine Parametersuche.
Alle Modelle auf identischen Zielzeitpunkten.
Keine Modellwahl anhand der Ergebnisse.

## Chronologische Validierung
Erstes Trainingsfenster:
2024-09-01 bis 2025-03-01 exklusiv.
Erste Evaluation: März 2025.
Danach monatliche Evaluation bis
2026-07-01 exklusiv, expanding training.
Modell jeweils nur zu Monatsbeginn neu schätzen.
Trainingslabels müssen vor Beginn der
jeweiligen Evaluation vollständig bekannt sein.
Kein randomisiertes K-Fold.
Keine finale unabhängige Bestätigung.

## Primäre Statistik
Mittlerer OOS-Quadratfehler.
Delta = MSE(B1) - MSE(M1).
Positive Werte begünstigen M1.
Relative Verbesserung = Delta / MSE(B1).
Unsicherheit: HAC mit Lag 12, vorab fixiert.
Zusätzliche Robustheit: Kalenderwochen-
Blockbootstrap, 2000 Wiederholungen,
Seed 20261114.
Verschachtelte Modelle: HAC der rohen
Verlustdifferenz nicht als allgemeingültigen
klassischen Diebold-Mariano-Test ausgeben.
Keine nachträgliche Auswahl des günstigeren Tests.

## Erfolg und Abbruch
Explorative Evidenz nur bei positiver
Delta-Schätzung und 95%-Intervall oberhalb null.
1% relative Verbesserung als zusätzliches
vorläufiges Relevanzziel; kein Beweis
wirtschaftlicher Handelbarkeit.
Unabhängige Bestätigung benötigt neue Daten.
Keine zusätzlichen Modelle bei negativem Befund.
Keine Strategie- oder Orderableitung.

## Reproduzierbarkeit
Input-Hashes aus 01_DATENINVENTUR.txt.
Code- und Laufzeitversion beim Forschungslauf sichern.
Ergebnisse, Negativbefunde und Versuche registrieren.
Originaldaten ausschließlich lesend.


## V3: Methodische Korrekturen vor Datenmessung

1. Prognosezeitpunkt nach Abschluss von t.
   ETH-Lags: t, t-1, t-2.
   BTC-Lags: t, t-1, t-2.
   Ziel: ETH-Rendite t bis t+1.
   Alle Koeffizienten ausschließlich aus der Vergangenheit.

2. Primärer Effekt:
   Relative OOS-MSE-Verbesserung gegenüber ETH-AR(3).
   Effektgröße und 95%-Intervall berichten.

3. Ergänzende Inferenz:
   Clark-West-adjustierte Verlustdifferenz
   für verschachtelte Prognosemodelle.
   HAC-Lag 12, einseitige gerichtete Prüfung.
   Annahmen und Stichprobeneignung auditieren.
   Kein unkritischer Standard-DM-Test.

4. Robustheit:
   Kalenderwochen-Blockbootstrap,
   2000 Wiederholungen, Seed 20261114.
   Keine nachträgliche Blocklängenoptimierung.
   Bootstrap-Intervall der relativen Verbesserung.

5. Die 1%-MSE-Verbesserung ist ein vorläufiger
   Relevanzmaßstab, kein belegter Handelsvorteil
   und kein alleiniger Bestätigungsmaßstab.

6. Evaluationsmonate März 2025 bis Juni 2026.
   Expanding Training ab September 2024.
   Training nur mit vollständig verfügbaren Labels.
   Keine Neuoptimierung von Fensterlängen.

7. Bekannte historische Tests:
   R1, R2 und R3 berücksichtigen.
   R4-Lead-Lag-Vorversuche nicht abschließend
   inventarisiert. Keine Blindtest-Behauptung.

8. Fehlende received_at-Zeitstempel:
   Keine Aussage zu realer Empfangslatenz
   oder wirtschaftlicher Ausführbarkeit.

9. Abbruch:
   Modell- oder Zeitfehler, fehlende
   Datenprovenienz oder unzureichende
   statistische Auswertbarkeit.

10. Status:
    Explorative Forschung nach Methodenaudit.
    Unabhängige Bestätigung benötigt neue Daten.
    Noch keine Messfreigabe.
