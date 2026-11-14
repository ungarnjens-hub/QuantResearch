# R8-BX: Explorative BTC→SOL-Richtungsprognose, v1.0

Datum: 14.11.2026. **Explorativ / Daten bereits verwendet / KEIN Blindtest.** Getrennt von R8-B; dessen reservierter Testzeitraum April–Juni 2027 und sein Trainings- und Sperrplan bleiben unberührt.

## Forschungsfrage
Verbessern die letzten drei **abgeschlossenen** 5-Minuten-BTC-Renditen die probabilistische Vorhersage der Richtung der **nächsten** SOL-5-Minuten-Rendite gegenüber den letzten drei SOL-Renditen allein?

H0: Kein positiver Out-of-sample-Log-Loss-Gewinn M1 gegenüber B1. H1: Positiver Gewinn. **Explorative Auswertung, ohne formale confirmatory Signifikanzbehauptung**. Selbst ein positiver Befund auf diesen verbrauchten Daten würde keinen kausalen BTC-Vorlauf, keinen Gewinn und keinen unabhängig bestätigten Effekt bedeuten.

## Datensatz und Trennung
- Originaldateien, **nur lesend**: `~/QuantResearch/Validation_2026_AugOct/data/{BTC,SOL}_USDT_5m_2026-07_2026-10.parquet` samt `manifest.json`; Binance USD-M Perpetual, `last_trade`, `/fapi/v1/klines`, vollständiges 5-Minuten-UTC-Raster.
- Training: Juli 2026. Auswertung: August–Oktober 2026, bereits in R5/R6 und R8-A benutzt. Drei Fits jeweils zu 1. August, 1. September, 1. Oktober 00:00 UTC, expandierendes Training nur mit dann bekannten Labels.
- **Kein** Datenzugriff Januar–Juni 2027. Kein Wechsel der Perioden nach Ergebniskenntnis. Ausschließlich Daten bis inklusive letzte vollständig geschlossene Kerze je Entscheidungszeitpunkt.

## Modelle und Verluste
- Feature-Berechnung exakt nach `R8_phase_b_synthetischer_e2e_test.py`, SHA256 `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff` (Open-Time → Close-Time, 3 SOL- bzw. BTC-Renditen, Label nächste Kerze).
- B0: Trainingsanteil positiver Nichtnull-Renditen; B1: logistische Regression aus 3 SOL-Lags; M1: B1 + 3 BTC-Lags. Trainingsbasierte Standardisierung, keine Regulierung; keine Nachoptimierung; Nullzielrenditen nur aus Score entfernen, aber Prognosen vorher erstellen und zählen.
- Primär: Δ = durchschnittlicher LogLoss(B1) minus LogLoss(M1) bei Nichtnull-Ziel; sekundär B0/B1/M1, relative Verbesserung, Genauigkeit bei 0,5, Nullzählung.
- Diagnoseintervall für Δ: gepaarte 7-Kalendertage-Moving-Block-Bootstrap auf Tages-Summen und -Nennern; 5000 Resamples, `default_rng(20261114)`. Kein confirmatory p-Wert.

## Harte Gates
- Code und Protokoll vor erstem Ergebnis **git commit + push**; SHA256 prüfen.
- Rohdateien: Manifest-SHA256, Identität und 35.424 lückenlose UTC-5-Minuten-Kerzen, OHLCV-Konsistenz und positive Preise. Bei Abweichungen FAIL-CLOSED.
- Gleiches Raster beider Märkte, kein Fill, kein impliziter Join; Trainingslabels zu jedem Refit verfügbar; genau 92 Bewertungstage, letzte Periode ohne unbekanntes Folgelabel; keine Neuberechnung in existierendem Ergebnisordner.
- Alle Resultate einschließlich negativer Ergebnisse berichten. Kein produktiver Datei- oder Bot-Zugriff; keine Handelsstrategie.

## Entscheidung
Der Vorversuch liefert allenfalls **explorative** Orientierung. R8-B bleibt **nicht freigegeben** für einen echten unabhängigen Test. R8-B-Protokoll und Blindtestzeitraum bleiben unverändert; ein R8-BX-Resultat darf nicht zur rückwirkenden Verbesserung der Hauptprüfung verwendet werden.
