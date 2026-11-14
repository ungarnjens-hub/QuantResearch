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
