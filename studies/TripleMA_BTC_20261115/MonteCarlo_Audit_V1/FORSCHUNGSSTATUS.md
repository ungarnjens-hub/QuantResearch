# Triple-MA BTC: Monte-Carlo-Risikoaudit V1

Status: Explorativ abgeschlossen. Robustheit nicht bestätigt.
Keine Strategieoptimierung, keine Handelsfreigabe.

## Untersuchungsgrundlage
BTC/USDT Binance Futures, eingefrorene Triple-MA-Strategie.
Entwicklung 2024–2025: 115 Trades, +23,0044 USDT, PF 1,4053.
Zeitlich getrennter Test 2026: 31 Trades, +8,1742 USDT, PF 1,6212.

## Methode
10.000 Blockbootstrap-Simulationen je Szenario.
Kalenderwochenblöcke: 1, 2 und 4 Wochen.
Zusatzkosten: 0, 2, 5 und 10 Basispunkte pro Roundtrip.
Entwicklungs- und 2026-Daten getrennt ausgewertet.

## Hauptergebnisse
Bei 2-Wochen-Blöcken und ohne Zusatzkosten:
- Entwicklung: 8,88 % negative Simulationen; Netto-q05 -4,968 USDT.
- 2026: 20,09 % negative Simulationen; Netto-q05 -5,079 USDT.
- 2026 mit zusätzlichen 10 bp: 28,63 % negative Simulationen.

Gewinnkonzentration:
- Entwicklung ohne drei größte Gewinner: -1,665 USDT.
- 2026 ohne größten Gewinner: -0,769 USDT.
- 2026 ohne drei größte Gewinner: -6,150 USDT.

## Wissenschaftliche Einschränkungen
Bootstrap-Häufigkeiten sind keine verlässlichen zukünftigen
Verlustwahrscheinlichkeiten. Die 2026-Daten sind bereits ausgewertet
und kein unverbrauchter Blindtest mehr.

Drawdowns basieren auf geschlossenen Trades.
Stop-Ausführung, Slippage, Gebühren und Funding sind nicht vollständig
unabhängig validiert. Die Gewinnkonzentration ist hoch.

## Entscheidung
Kandidat bleibt ungeklärt. Parameter unverändert einfrieren.
Keine Optimierung anhand der 2026-Validierung.
Nächster unabhängiger Nachweis benötigt neue Forward-Daten.

Originaldaten und vollständige Simulationsergebnisse:
results_v1/report.json
