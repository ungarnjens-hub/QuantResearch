# R16 BTC: Vortageshoch/Vortagestief und die Reichweite bestätigter Reaktionen

**Status:** Exploratives Vorabprotokoll (Phase A/B); keine echte Marktmessung vor Commit.

## Forschungsfrage und plausibler Mechanismus

Ist bei BTC/USDT Binance USDT-M Futures nach einer Berührung des **Hochs (PDH)** oder **Tiefs (PDL)** des bereits abgeschlossenen vorangegangenen UTC-Kalendertages und einer einfachen, beobachtbaren Umkehrbestätigung eine wirtschaftlich nutzbare, richtungsabhängige Folgekursbewegung sichtbar? Wie weit läuft der Preis und wann tritt der Maximalwert ein? Hintergrundhypothese: Häufung von bedingten Orders an auffälligen Preisniveaus kann Reaktionen oder Kaskaden verursachen. Diese aus Devisen belegte Mikrostruktur ist **für BTC nicht bewiesen**. Fachquelle: C. L. Osler, *Currency Orders and Exchange Rate Dynamics*, Journal of Finance 58(5), 2003, 1791–1819, DOI 10.1111/1540-6261.00588.

## Festgelegte Population und Daten

BTC/USDT USDT-M perpetual, last-trade 5m OHLCV, lokal canonical, Sep 2024 bis Dez 2025, 16 Monatsdateien. R12-Frozen-Loader (SHA-256 `7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d`) prüft Uhrzeit, vollständige Kerzen, Duplikate, Lücken und Datenherkunft. Keine produktiven Dateien ändern. Tageskerzen werden aus **00:00–24:00 UTC** abgeschlossen gebildet, nicht nach örtlicher Zeitzone. Der erste Kalendertag Sep 2024 besitzt keine Vor-Tageskerze und ist daher nicht auswertbar. Ende jedes Jahres nur vollständige künftige 24h-Labels; keine Grenzenüberschreitung.

## Ereignisse vorab definiert

PDH/PDL sind exakte historische Tageshöchst-/-tiefpreise des **vorigen** UTC-Tages, ohne nachträgliche Zonenverschiebung. Beobachtungszeitraum: erster tatsächlicher Anlauf/Kontakt des Niveaus an jedem UTC-Tag pro Niveau, erkennbar aus vollständiger 5m-Kerze. PDH: vorheriger abgeschlossener 5m-Schluss unter PDH und aktuelle Hochberührung; PDL entsprechend umgekehrt. Falls die erste Tageskerze schon über PDH bzw. unter PDL öffnet, wird nur ein späterer echter erneuter Anlauf erkannt; kein rückwirkend erfundener Limit-Fill. Je UTC-Tag sind höchstens zwei Chancen im Katalog (PDH und PDL), Überlappungen zwischen den beiden Gruppen sind möglich und werden nicht additiv als Portfolioertrag dargestellt.

**Referenz**: sofortiger theoretischer Einstieg auf der nächsten 5m-Eröffnung, Short an PDH, Long an PDL. **Bestätigung**: innerhalb der folgenden drei abgeschlossenen 5m-Kerzen Kerzenschluss zurück innerhalb der vorherigen Tagesrange (PDH: unter PDH, rot, unter vorherigem Schluss; PDL: über PDL, grün, über vorherigem Schluss). Schlusskurs mindestens 15bp auf der falschen Seite des Levels bricht zuvor die Reversal-Hypothese. Kein Einstieg ohne Bestätigung. Confirmation Entry auf Eröffnung **nach** dieser Kerze.

## Diagnostik des Preiswegs und ausführungssimulierter Vergleich

- Ab jeweiliger Entry-Eröffnung maximale günstige Bewegung (MFE) und maximale ungünstige (MAE) innerhalb 60m, 120m und 24h; zusätzlich 75%- und 90%-Perzentil der MFE und Zeitspanne vom Entry bis zur 5m-Kerze des MFE-Peaks. Das ist *nachträgliches, nicht ausführbares Kursmaximum*.
- Ein weiteres festes, nur diagnostisches Simulationsmodell: Stop hinter dem seit Kontakt beobachteten Extrem plus 0,25 ATR(14); Take Profit 2R; Ende zur 120-Minuten-Eröffnung. Risiko muss positiv und Stoppreis >0 sein. Bei Stop/TP in derselben Kerze gewinnt Stop. Bei ungünstiger Eröffnungslücke gilt diese Lücke, bei TP-Lücke konservativ TP. Die Daten erlauben keine Tick-Reihenfolge.
- Kosten: 14bp pro Roundtrip Basismodell, 24bp Stresstest; keine echten historischen Gebühren, Funding oder Slippage-Abrechnungen. Ausführungsergebnisse sind Szenarien, **keine bewiesene Netto-Profitabilität**.
- Immer die Anzahl der Ursprungskontakte und der bestätigten/abgebrochenen/nicht bestätigten Fälle nennen; pro Ursprungskontakt bleibt ein Nicht-Trade bei 0. Keine nachträgliche Auswahl eines „optimalen“ Zielwerts aus den MFE-Verteilungen.

## Prüfkriterien und Audit

1. Original-Loader-Audit, UTC-Tagzuordnung, ausschließlich Vortageswerte und echter nächster Open.
2. Synthetikchecks: künftige Highs ändern die Vor-Tageszone nicht; MFE Peak, Stop, TP, ungünstige Lücke, same-bar Konflikt, Ablauf und Periodengrenze.
3. Getrennte Ergebnisse 2024 und 2025 für PDH/PDL; nur deskriptiv. 2024/2025 wurden mehrfach zuvor analysiert, deshalb kein unbenutzter Blindtest und keine erneute bestätigende Statistik.
4. Primäres praktisches Kriterium: konservativ simuliertes Netto/Trade, Netto/Ursprungskontakt und Stop/TP-Frequenz müssen in **beiden** Zeitperioden positiv bzw. günstig sein, um überhaupt einen Kandidaten für spätere unabhängige Validierung zu rechtfertigen. Positive MFE ohne günstige Exekution gilt **nicht** als Strategiegewinn.
5. Negative Ergebnisse unverändert dokumentieren. Keine Auswahl nach bestem Jahres-/Seiten-/Zeitfenster ohne neue Explorationsoffenlegung. Vermeidung von Data Snooping und Overfitting.

## Artefakte

`R16_PDH_PDL_EVENTS.csv`: Ereignisdetails; `R16_RESULTS.json`: Parameter, Quellhashes, aggregierte Messwerte; `R16_REPORT.md`: Bericht. Isolation in `~/QuantResearch/R16_BTC_PDH_PDL/Sep2024_Dec2025_v1`. Originale TradingLab/Paper/Freqtrade-Dateien unverändert.
