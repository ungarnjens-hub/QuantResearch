# Triple-MA BTC: Risiko- und Robustheitsaudit V1

**Status:** Phase A (Forschungsdesign), Phase B (Methodenaudit, lokale ZIP-Prüfung noch offen). **Keine neue Ergebnismessung durchgeführt.**
**Datum:** 2026-11-15. Forschungsbereich ausschließlich; keine Handelsfreigabe und keine Strategieoptimierung.

## Ausgangspunkt und Falsifizierbarkeit
Die *eingefrorene* Freqtrade-2026.9-Strategie `TripleMA_BTC_V1_ATR15_Complementary_Hours` wird unverändert anhand bereits gespeicherter Backtest-Trades beurteilt. Markt BTC/USDT Binance USD-M Perpetual; Long außerhalb 12–17 Uhr UTC, Short ausschließlich 12–17 Uhr UTC; EMA 7/25/200, anfänglicher 1,5× ATR(14)-Stop, Trend-only. Die vorab bekannten Referenzen sind Entwicklung: 115 Trades, +23,00436 USDT, PF 1,40533; 2026-01-01 bis 2026-06-30: 31 Trades, +8,17416365 USDT, PF 1,6212.

**H0:** Die beobachteten positiven Nettogewinne könnten vollständig durch Stichprobenvariation eines schwachen oder nicht vorhandenen Vorteils erklärt werden. Das Verfahren liefert *keinen formellen Test* dieser Nullhypothese; es beschreibt die empirische Unsicherheit unter Resampling-Annahmen.

**H1 (Risikohypothese):** Unter zeitabhängigkeitserhaltendem Resampling und vorgegebenen Zusatzkosten bleibt das Nettoergebnis überwiegend positiv; die schlechten Ergebnisse sind begrenzt. Ein gravierender Anteil negativer Bootstrap-Ergebnisse, negative untere Quantile, oder Abhängigkeit von sehr wenigen Ausreißern sprechen gegen Robustheit, **nicht** automatisch gegen Existenz eines Vorteils.

**Vermuteter Mechanismus:** Trendfortsetzung und asymmetrische Verteilung weniger größerer Gewinner durch EMAs und gegliederte Zeitsessions. Dies ist bislang eine Arbeitshypothese, keine bewiesene kausale Erklärung.

## Daten, Isolation und Identität

Zwei bereits vorhandene Freqtrade-ZIP-Archive werden unverändert und rein lesend geöffnet:

1. `~/QuantResearch/TripleMA_Complementary_Hours_AB_V1/user_data/backtest_results/backtest-result-2026-11-15_16-16-55.zip` (Entwicklung)
2. `~/QuantResearch/TripleMA_2026_Frozen_Test_V1/user_data/backtest_results/backtest-result-2026-11-15_16-24-25.zip` (2026, **bereits konsumierter** zeitlich getrennter Test)

Nur die exakt benannte Strategie wird extrahiert. SHA256 der Ursprungs-ZIPs, Zeitstempel, Duplikate, Währung, Realisierung der Trades, Anzahl und bekannte Summen werden auf Plausibilität geprüft. Für Gebühren-Stress wird `stake_amount × leverage` als Näherung des Handelsnotionals verwendet; falls diese Felder fehlen, ist der Lauf BLOCKED. Bereits in `profit_abs` berücksichtigte Gebühren werden *nicht entfernt*; die nachfolgenden Kosten sind zusätzliche hypothetische Rundlauf-Belastungen.

**Nicht nachgewiesen durch dieses Audit:** Korrektheit des ATR-Stops auf Intrabar-Ebene, Funding, Liquidität, Slippage der ursprünglichen Backtests, Futures-Liquidation, parallele Exposition, Mark-to-Market-Drawdown und Forward-Fähigkeit. Diese Fragen brauchen einen getrennten Freqtrade-Code-/Daten-Audit. Bei mehreren gleichzeitigen Trades ist eine Folge geschlossener Trade-PnLs keine exakte Portfolio-Equitykurve.

## Fixiertes Untersuchungsdesign

- Auswertung **getrennt** für Entwicklung und 2026, kein Pooling für einen vermeintlich größeren Blindtest.
- Kalenderwochen (UTC, Montag–Sonntag), einschließlich Wochen ohne Trades, anhand des **Schließdatums** der Trades. Trades werden innerhalb jeder Woche nach Close-Zeitpunkt sortiert.
- Zirkulärer **Moving-Block-Bootstrap** (MBB) über die Kalenderwochen: mit Zurücklegen gezogene zusammenhängende Wochenblöcke; für die letzte Woche zirkulär. Hauptanalyse 2 Wochen, Sensitivität 1 und 4 Wochen.
- `10.000` Wiederholungen je Fenster, Blocklänge und Kostenannahme; deterministische Seeds aus `20261115`.
- Zusätzliche Kosten je Trade: `0`, `2`, `5`, `10` Basispunkte **Rundlauf** auf `stake_amount × leverage`. Keine ex-post Auswahl der Belastungsstufe.
- Berichtet: empirischer Netto-PnL, PF, Netto-PnL-Quantile 1/5/50/95/99 %, Anteil resampelter Netto-Verluste, Profit-Faktor-Quantile soweit definiert, Drawdown aus kumulierten **abgeschlossenen** Trades, größter Gewinner, Top-3-Gewinner und Netto ohne diese Gewinner (Sensitivitätsdiagnose, keine handelbare Regel).
- Vergleichsmaßstab: Null-Nettoergebnis nach Kosten und Null-Informationsannahme. Kein vorgetäuschter Strategiebenchmark ohne entsprechende Backtest-Datei.

## Vorab festgelegte Interpretation

- **Keine harte Bestehensregel und keine Handelsfreigabe** anhand dieser kleinen, bereits selektierten Stichprobe. Bewerte die Breite der Verteilungen, die Quote negativer Stichproben, und die Sensitivität auf Blöcke und Zusatzkosten.
- Besteht eine starke Abhängigkeit von wenigen Gewinnern oder fallen die unteren 5%-Quantile deutlich ins Negative, lautet die Bewertung "Robustheit ungeklärt/fragil", auch wenn der beobachtete PF > 1,4 beträgt.
- Resultate aus 2026 bleiben Resultate desselben **schon betrachteten** Holdouts. Neue Exit-/EMA-Varianten dürfen dort nicht als unberührte Validierung getestet werden. Ein neuer Forward-Zeitraum ist erforderlich.
- Die Bootstrap-Annahme ähnlicher zukünftiger Wochen, der geringe Umfang (2026: etwa 26 Wochen) und die vergangene Auswahl unter mehreren getesteten Varianten können die Güte der Schlussfolgerungen erheblich begrenzen.

## Workflow

1. **Phase A:** Dieses Dokument festhalten (keine Messung).
2. **Phase B:** `--audit` ausführen, ausgegebene Dateihashes/Zeiträume/Summen sowie Strategie- und Ausführungssemantik kontrollieren. Probleme beheben, bevor irgendeine Monte-Carlo-Messung erfolgt.
3. **Phase C:** Erst nach ausdrücklicher Freigabe `--run` ausführen. Alle Dateien außerhalb eines dedizierten Forschungsverzeichnisses unangetastet lassen.
4. **Phase D:** `report.json` kritisch mit Quantilen, Unsicherheit und methodischen Grenzen auswerten.
5. **Phase E:** Nur bei ausreichender Begründung neue noch unbekannte Forward-Daten nach festgelegter Regel untersuchen.
6. **Phase F:** Auditcode, Versionen, Dateihashes, Ergebnisse und Negativbefunde versioniert archivieren.

## Fachgrundlagen

- Politis & Romano (1994), *The Stationary Bootstrap*, Journal of the American Statistical Association, DOI 10.1080/01621459.1994.10476870. Referenz für abhängige Zeitreihen-Resampling-Verfahren. **Hier kommt der verwandte, aber nicht identische Moving-Block-Bootstrap zum Einsatz.**
- Freqtrade Dokumentation, *Backtesting* (aktuelle Seite), https://www.freqtrade.io/en/stable/backtesting/ (Exportformat, Gebühren, Kontext von Backtest-Ergebnissen).
- Freqtrade Dokumentation, *Backtest analysis*, https://docs.freqtrade.io/en/latest/advanced-backtesting/ (Trade-Felder und Analyse historischer Resultate).
