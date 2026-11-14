# R6: BTC -> SOL Volatilitaet
Status: PHASE B - METHODIK FIXIERT
Datum: 2026-11-14

## Forschungsziel
Inkrementeller Prognosewert vergangener BTC-
Volatilitaet fuer zukuenftige SOL-Volatilitaet.

## Methodik
Uebertragung der R5-Modellfamilie auf SOL.
Nur die Zielmarktbezeichnung ETH -> SOL aendern.

5m-Kerzen, 60m-Prognosehorizont.
Prognose einmal je Stunde.
HAR-RV-Fenster: 12, 288, 2016 Kerzen.
Logarithmierte Realized Variance.
OLS mit Intercept.

B0: Historischer SOL-Zielmittelwert.
B1: SOL-HAR-RV.
M1: SOL-HAR-RV plus BTC-RV.

## Zeitliche Validierung
Training ab 2024-09-01 UTC.
Evaluation 2025-03-01 bis 2026-07-01 exklusiv.
Monatliches expandierendes Walk-Forward.
Nur vor Evaluationsbeginn verfuegbare Labels.
Keine Parameteroptimierung.

## Primaerer Endpunkt
Relative MSE-Verbesserung M1 gegen B1
auf dem logarithmierten 60m-RV-Ziel.

## Statistik
Gepaarter vierwoechiger Moving-Block-Bootstrap.
2000 Wiederholungen, Seed 20261114.
95%-Perzentilintervall.
Clark-West/HAC mit vier Lags sekundaer.
Alle Ergebnisse inklusive Negativbefunde berichten.

## Entscheidung
Explorativ positiv nur bei positiver Verbesserung
und Bootstrap-Untergrenze ueber null.
Andernfalls nicht gestuetzt oder unklar.
Keine unabhaengige Bestaetigung auf bekannten Daten.

## Datenherkunft
SOL-Futures-OHLCV intern per SHA256 verifiziert.
Urspruenglicher Binance-Abruf nicht direkt belegt.
Last-Trade-Preisquelle bleibt eine Annahme.
Kein Vergleich von Markpreis- und Last-Trade-Daten.

## Abbruch
STOP bei Abweichungen von R5 ausser dem
Zielmarktwechsel und notwendigen Dateiadaptern.
STOP bei Zeitfehlern oder Zukunftsinformationen.
Keine Optimierung nach Ergebniseinsicht.

## Schutz
Nur isolierte Forschung.
Keine produktiven Dateien oder Bots veraendern.

## Freigabestatus
Methodischer Entwurf fixiert.
Ausfuehrungsimplementierung und notwendige
Datenadapter muessen vor Ergebnismessung
mit synthetischen Daten geprueft werden.
