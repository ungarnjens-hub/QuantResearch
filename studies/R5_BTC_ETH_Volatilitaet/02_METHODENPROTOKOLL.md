# R5 Methodenspezifikation
Stand: 2026-11-14
Status: Phase B, vor Messfreigabe

## Forschungsgegenstand
Prognose der ETH-Realized-Variance über die
nächsten 60 Minuten durch vergangene ETH-
und BTC-Volatilitätsinformationen.

## Beobachtungszeitpunkte
Eine Prognose pro Stunde.
Nur vollständig abgeschlossene 5m-Kerzen.
Zeitpunkt t bezeichnet die letzte bekannte
Kerze unmittelbar vor der vollen UTC-Stunde.
Keine überlappenden Evaluationsziele.

## Zielvariable
RV_ETH(t+1:t+12) =
Summe der quadrierten ETH-5m-Logrenditen
der nächsten zwölf Kerzen.

Regression auf log(RV + 1e-12).
Vorhersagen per exp() - 1e-12,
bei Bedarf auf null begrenzen.
Numerische Konstante vorab fixiert.

## Features
Für ETH und BTC jeweils:
RV12: letzte 12 abgeschlossene 5m-Renditen.
RV288: letzte 288 abgeschlossene Renditen.
RV2016: letzte 2016 abgeschlossene Renditen.

Jeder Wert wird durch seine Fensterlänge geteilt.
Transformation: log(RV-Mittel + 1e-12).
Keine globalen Normalisierungen.

## Modelle
B0: Historischer Mittelwert der Zielvariable
aus ausschließlich verfügbaren Trainingsdaten.

B1: ETH-HAR-RV mit drei ETH-Features.
M1: B1 plus drei BTC-RV-Features.

OLS mit Intercept.
Keine Hyperparametersuche.
Alle Modelle auf identischen Zeitpunkten.

## Chronologisches Walk-Forward
Trainingsbeginn: 2024-09-01 UTC.
Erste Evaluation: 2025-03-01 UTC.
Letzte Evaluation: Juni 2026.

Monatliche Neuschätzung, expandierendes Training.
Trainingslabels müssen vor dem Trainingsstichtag
vollständig beobachtet sein.
Auswertungsziele dürfen niemals ins Training
desselben Monats gelangen.
Keine zufällige Kreuzvalidierung.

## Primärer Endpunkt
Mittlerer quadratischer Fehler auf der
logarithmierten Zielvariable.
Vergleich M1 gegen B1.
Relative MSE-Verbesserung in Prozent.
B0 als zusätzliche Referenz.

## Unsicherheit
Gepaarter Moving-Block-Bootstrap auf
Kalenderwochen, vier Wochen je Block.
2000 Wiederholungen, Seed 20261114.
Randwochen eingeschlossen.
Aggregation über Einzelprognosen.
95%-Perzentilintervall der relativen Verbesserung.

## Sekundäre Prüfung
Clark-West-adjustierter Prognosevergleich
für verschachtelte lineare Modelle.
HAC mit vier Lags auf stündlichen Fehlern.
Einseitige Hypothese positiver Zusatzinformation.
Der Test ersetzt nicht die primäre Effektgröße.

## Entscheidung
Explorative Evidenz nur bei positivem
primärem Effekt und 95%-Intervall oberhalb null.
Sonst nicht gestützt beziehungsweise unklar.
Ohne neuen Blindtest keine unabhängige Bestätigung.

Keine Profitabilitätsaussage.
Keine nachträgliche Parametersuche.
Bekannte R1/R4-Befunde ausdrücklich berücksichtigen.

## Technische Stopregeln
Abbruch bei Zeitfehlern, inkonsistenten
Features, überlappenden Trainingslabels,
nicht reproduzierbaren Rechenergebnissen
oder fehlerhaften Modellvergleichen.

Keine Änderung an TradingLab, Freqtrade
oder Originaldaten.
