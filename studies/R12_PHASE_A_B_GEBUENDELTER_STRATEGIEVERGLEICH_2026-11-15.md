# R12: BTC-Futures, drei einfache Strategietypen unter gleichen Bedingungen
**Forschungsprotokoll und Methodenaudit, 15.11.2026, v1.0**

**Status:** vorab spezifizierter, einmaliger, **explorativer** historischer Vergleich. Kein Paper-/Live-Trading, keine Orderausführung, keine operative Strategieempfehlung. Die vorliegende Forschungsserie untersucht nur Marktdaten in einem isolierten Verzeichnis. Nachträgliche Parameteränderungen ergeben eine neue, separat registrierte Studie und keine Wiederholung auf einem unverbrauchten Datensatz.

## 1. Neue Forschungsfrage
Kann **eine von drei einfachen, vollständig regelgebundenen Handelsansätzen** bei BTCUSDT-Perpetual-Futures in 2024 und 2025 unter **denselben konservativen Kostenannahmen** einen **positiven simulierten Netto-Erwartungswert je Trade** und akzeptable Verluste zeigen? Wir untersuchen die wirtschaftliche Wirkung von Entry, Stop, Ziel und Zeitlimit zusammen, nicht bloß die Richtung der nächsten Kerze. Die drei Regeln sind **Forschungskandidaten**, keine optimierten professionellen Strategien.

Null je Strategie: durchschnittlicher simulierter Netto-PnL pro Trade ist nicht positiv. Es werden keine kalibrierten konfirmatorischen Nulltests behauptet, denn die Daten wurden in früheren Forschungsreihen mehrfach gesehen, und drei Kandidaten konkurrieren um dieselbe Chance.

## 2. Fachgrundlage und Begrenzung
Trendfolge, Range-Breakout und Mean Reversion sind bekannte Klassen technischer Handelsregeln. Dies ist **keine** Behauptung, dass die unten ausgewählten numerischen Schwellen Literaturstandards sind; sie sind einfache, vorab fixierte Beispieldefinitionen. Mehrfachvergleich und Nachselektion verursachen Backtest-Overfitting: Bailey et al. (2017), *The Probability of Backtest Overfitting*, DOI 10.21314/JCF.2016.322. Reale Funding-Historie für Binance USD-M ist laut Dokumentation über `/fapi/v1/fundingRate` abrufbar. Ohne verifiziert vorliegende Funding-Zahlungen ist die unten beschriebene **Kostenreserve keine gemessene Funding-PnL**. Es wird daher nur eine **indikative Nettosimulation unter Annahmen** berichtet.

## 3. Population und Datenverwendung
**Nur BTCUSDT**, Binance USD-M linear perpetual `last_trade` 5m OHLCV aus den 16 monatlichen kanonischen Parquet-Dateien, September 2024 bis Dezember 2025, jeweils nur vollständig abgeschlossene UTC-Kerzen. Originaldaten unter `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m/` werden **nur gelesen**. Prüfungen: vollständiges 5m-Raster, `close_time+1ms=open_time+5min`, 140.256 Kerzen, Schema/Herkunft, positive finite OHLC, Konsistenz, eindeutige Zeitstempel, Datei-SHA256. Fehlende Daten: fail closed, niemals Forward-Fill.

Perioden: `2024_SepDec` = September bis Dezember 2024; `2025_JanDec` = Januar bis Dezember 2025. **Beide explizit explorativ.** Keine Auswahl eines Siegers von 2024, um 2025 nachträglich als Blindtest auszugeben. Erste 300 Kerzen je Abschnitt als Warm-up; vor-periodisch ermittelte historische EMA und ATR könnten in der Praxis bekannt sein, der Runner verhindert zusätzliche Starttrades durch die Warm-up-Sperre. Keine Position läuft über eine Abschnittsgrenze.

## 4. Drei exakt fixierte Einstiegssignale (alle auf abgeschlossenen 5m-Kerzen)
Index `j`: zuletzt vollständig abgeschlossene 5m-Kerze. Alle `EMA`, `ATR`, Rolling-Extrema und Preisbedingungen werden mit Preisen bis einschließlich `j` berechnet.

- **P1 Trend-Pullback:** EMA12 > EMA48 und `ln(C[j-1]/C[j-4]) <= -0,001` sowie aktuelle Kerze `C[j]>O[j]` => Long. Symmetrisch EMA12 < EMA48 und 3-Kerzen-Vorlauf `>= +0,001` und `C[j]<O[j]` => Short. Der Vorlauf endet ausdrücklich bei `j-1`.
- **P2 Range-Breakout:** Schluss `C[j]` über dem höchsten Hoch der **12 vorherigen** 5m-Kerzen `H[j-12:j]` und grüne Signal-Kerze => Long. Symmetrisch unter niedrigstem Tief und rote Signalkerze => Short.
- **P3 Mean Reversion:** `I[j]=ln(C[j]/C[j-6])`; `z[j]=abs(I[j])/(sqrt(6)*std(r[j-294:j-6],ddof=1)) >= 2`. Historische **288** 5m-Renditen enden vor Impulsbeginn; aufwärtsgerichteter Impuls => Short, abwärtsgerichteter Impuls => Long. Null- oder ungültige SD und Nullimpuls = kein Signal.

Es gibt **keinen** Timeframe- oder Session-Filter, keine nachträgliche Optimierung, kein Volumenfilter, keine Suche nach den besten Schwellen. Die drei Signaltypen sind unabhängig; für jeden wird eine eigene isolierte Vergleichs-PnL-Reihe simuliert, **keine Kombination zu einem Portfolio**.

## 5. Einheitliche Ausführung und Risikoannahmen
- Signal nach Kerzenschluss `j`, frühestmöglicher Entry **Open von j+1**; kein Handel im Signal-Bar.
- Pro Strategie nur eine offene Position, kein Hedge derselben Strategie; Signal während offener Position ignorieren, keine Wiedereintritt in Exit-Kerze.
- Fester nominaler Einsatz **100 USDT pro Trade** (kein Leverage angenommen), Modellkonto **10.000 USDT**. Kein Reinvestieren. Keine reale Kapitalbindung, Marginsimulation oder Liquidationsmodellierung.
- ATR14 aus vollständig abgeschlossenen Kerzen inklusive `j`; Stop-Abstand `1,5 * ATR14`, Zielabstand `3 * ATR14` vom nächsten Entry-Open. Ist ein Stop nicht positiv, kein Entry.
- Stop/TP prüft 5m Hoch/Tief ab Entry-Kerze. Wenn beide in derselben Kerze möglich sind, **Stop zuerst**. Bei einer gegenläufigen Eröffnungslücke über den Stop hinaus: schlechterer Eröffnungspreis. Zielverbesserungen durch günstige Gaps werden **nicht** gutgeschrieben.
- Zeitlimit zwölf volle 5m-Positionierungs-Kerzen. Falls kein Stop/TP: Exit **Open j+13**, also nach zwölf abgeschlossenen Kerzen. Trades, die über die Studienperiode reichen würden, werden nicht eröffnet.

## 6. Kosten, zwei vorher festgelegte Szenarien
Alle Werte **Annahmen**, nicht erhobene reale individuelle Binance-Kontokonditionen. Ein Basispunkt = 0,01 % Notional.

| Kosten je Trade | Basisszenario | Stressszenario |
|---|---:|---:|
| Gebühren pro Seite | 4 bp | 6 bp |
| Slippage pro Seite (adverser Kurs) | 2 bp | 4 bp |
| Funding-Reserve pro Roundtrip | 2 bp | 4 bp |
| Grober Rundreise-Kostenansatz | ~14 bp | ~24 bp |

Gebühren werden auf die modellierten tatsächlichen Fill-Notionalbeträge, Slippage auf Ein-/Ausstieg und eine positive pauschale Funding-Reserve auf jeden Trade angewandt. **Keine** Annahme, dass echte Fundingzahlungen regelmäßig positiv und in dieser Höhe waren. Der Simulationswert nach diesen Kosten heißt **„indikatives Netto nach Modellkosten“**, **nicht** belegter echter Netto-Backtest. Spread/Orderbuch, Ticks, Mark-Preis-Stopauslösung, Teilausführung, Latenz, Liquidation und echte Funding-Timestamps sind nicht vollständig modelliert; echte tradierbare Profitabilität bleibt offen.

## 7. Primäre Auswertung und Auswahlkriterien
Je Strategie und Teilperiode: Tradezahl, mittlerer Brutto-/Basis-/Stress-PnL pro Trade (USDT), mittlerer PnL in R, Trefferquote, Profitfaktor, Summen-PnL bei konstantem 100-USDT-Notional, Maximaldrawdown **nur geschlossener Trades**, Stop-/Ziel-/Zeitexits; 7-Tage-Kalenderblockbootstrap (2.000, Seed 20261115) für mittleren **täglichen** Basis-PnL einschließlich Tage ohne Trades. Die Intervalle sind **rein deskriptiv**, keine kalibrierten p-Werte oder Mehrfachtest-Korrektur. Nullposition als einfache Referenz (0 USDT Netto). Keine gemeinsame Portfolio- oder risikoadjustierte Buy-and-hold-Überlegenheit ableitbar.

**Vordefinierte Screening-Bedingung, nicht „profitabel bestätigt“:** mindestens 40 Trades im viermonatigen Abschnitt 2024 und 100 Trades im Jahr 2025, positive mittlere Basis-**und** Stress-Nettoannahme in **beiden** Abschnitten, positiver PF im Basisfall über 1 in beiden Abschnitten. Bei gemischten Zeichen oder fehlender Kostenrobustheit als „nicht überzeugend“ melden. Es gibt **keine** nachträgliche Gewinner-Optimierung; bei mehreren Kandidaten ohne neue Daten kein unbeeinflusster Sieger. Unabhängiger Test erst auf neuem, unberührtem Zeitraum nach getrenntem Design.

## 8. Technischer Audit und reproduzierbare Ausführung
Runner `R12_3_Strategien_BTC_Explorativ.py`: `--preflight` prüft nur künstliche Testdaten und Rohdatenintegrität, `--run` wiederholt Vorprüfungen, berechnet einmalig und schreibt isoliert unter `~/QuantResearch/R12_BTC_3Strategien/Sep2024_Dec2025_v1/`. Bestehendes Ergebnisverzeichnis => harter Stopp. Quellen/Code-SHA256, Versionsstände, alle einzelnen Trades, zusammenfassender JSON- und Markdown-Bericht werden archiviert. **Keinerlei** Freqtrade-API, Paper-Server, Orderausführung oder Netzwerkanbindung.

Synthetiktestumfang: Nächster Open statt Signalkurs, Stop-first bei derselben Kerze, adverser Gap, keine zukünftigen Features, keine periodengrenzüberschreitenden Trades, negative Kostenwirkung, nur eine Position je Strategie, konstante 7-Tage-Blockbootstrap-Kontrolle. Synthetiktests ersetzen keine unabhängige Prüfung realer Orderbuchfills.

**Status:** Forschungsdesign abgeschlossen und technischer Pilot auf vollständig synthetischer Zeitreihe geprüft. Echte BTC-Marktdaten wurden mit dem neuen Runner **noch nicht gemessen**. Ausführung des eingefrorenen `--run` ist nach erfolgreichem Preflight für die einmalige **explorative** Untersuchung freigegeben; keine konfirmatorische oder produktive Freigabe.

## Quellen
- Bailey et al., *The Probability of Backtest Overfitting*: https://doi.org/10.21314/JCF.2016.322
- Binance USD-M Funding Rate History: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
