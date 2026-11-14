# R4: BTC-ETH Lead-Lag
Datum: 2026-11-14
Status: Phase B - Methodenaudit, nicht freigegeben

## Forschungsfrage
Verbessern vergangene BTC-5m-Renditen die Vorhersage
der nächsten ETH-5m-Rendite?

## Marktmechanismus
Verzögerte Informationsübertragung von BTC auf ETH.
Alternative: gemeinsame Nachrichten und Scheinkorrelation.

## Hypothesen
H0: Kein zusätzlicher Prognosewert durch BTC.
H1: BTC verbessert die ETH-Prognose.

## Daten
Binance USD-M Perpetual, BTC/ETH, 5m, last_trade.
Gemeinsame Zeitachse: 198632 Kerzen.
Historische Datenqualität bereits geprüft.
R1/R2/R3 und frühere Analysen berücksichtigen.
Vorhandene Daten nicht als neuen Blindtest bezeichnen.

## Modelle
B0: Nullrendite.
B1: Lineares AR(3) nur mit ETH-Renditen.
M1: Lineares AR(3) mit zusätzlich drei BTC-Lags.
Keine Parametersuche.

## Prognose
Nach abgeschlossener Kerze t.
Ziel: ETH-Logrendite Close(t) bis Close(t+1).
Nur zu t verfügbare Informationen verwenden.
Ausführung und Empfangslatenz gesondert beachten.

## Primäre Bewertung
Out-of-sample-MSE relativ zu B1.
B0 als zusätzliche Referenz.
Vorgeschlagene Mindestverbesserung: 1 Prozent.
Diese Schwelle benötigt vor Messung eine Begründung.

## Validierung
Chronologische expandierende Fenster.
Trainingslabels müssen vor dem jeweiligen
Prognosezeitpunkt bekannt sein.
Überlappende Labels durch Purging ausschließen.
HAC-Unsicherheitsanalyse der Verlustdifferenzen.
Blockbootstrap als vorab spezifizierte Robustheitsprüfung.
Keine zufällige Kreuzvalidierung.

## Offene methodische Entscheidungen
1. Exakte Walk-Forward-Grenzen und Mindest-Trainingslänge.
2. HAC-Lagzahl und Bootstrap-Blocklänge.
3. Präzisions-/Powerprüfung und Mindestwirkung.
4. Vollständigkeit des historischen Versuchsregisters.
5. Neue, wirklich unabhängige Bestätigungsdaten.
6. Fehlende received_at-Zeitstempel berücksichtigen.

## Abbruchbedingungen
Keine Messung bei ungeklärten Informationszeitpunkten,
Datenüberschneidungen oder Modellfestlegungen.
Negative Resultate nicht nachoptimieren.

## Schutz
Keine Änderung an TradingLab, Freqtrade, Paper-Bots,
Originaldaten oder vorhandener Evidence.
