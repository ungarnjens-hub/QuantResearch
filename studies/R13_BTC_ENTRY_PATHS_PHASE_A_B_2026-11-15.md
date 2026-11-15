# R13 BTC Einstiegssignale: Kursverlauf, Gegenbewegung und Bewegungsraum
**Vorgeplantes Explorationsprotokoll und Methodenaudit, 15.11.2026**

**Forschungsziel:** Feststellen, ob die drei *unveränderten* Einstiegssignale aus R12 mit ausreichend günstigen **nachfolgenden** Preisverläufen verbunden sind, um eine später gesondert zu prüfende Handelslogik zu begründen. Nicht versuchen, den besten Stop, die besten Indikatoren oder den besten Ausstieg aus diesen historischen Daten zu optimieren. Kein Live-/Paper-Betrieb, keine Börsenzugriffe. Keine Veränderung produktiver TradingLab-Systeme.

## Phase A: Hypothese, Daten und Messgrößen

**H1 (falsifizierbar, explorativ):** Nach einem bestätigten Pullback-, Breakout- oder Reversion-Signal ist die *signierte* spätere BTC-Preisbewegung in derselben Richtung über vorab festgelegte Horizonte größer als bei einem tag-/zeitnahen zufälligen Einstieg ohne entsprechendes Signal in dieselbe Richtung. **H0:** Mittlerer Unterschied der Signale gegenüber der Referenz <= 0 bp. Die Untersuchung ist nur beschreibend, nicht als neues konfirmatorisches Testverfahren kalibriert.

**H2 (deskriptive Mechanismusprüfung):** Die günstige maximale Exkursion (MFE) und ungünstige maximale Exkursion (MAE) eines Einstiegssignals innerhalb von 15, 30, 60 und 120 Minuten lassen erkennen, ob das Signal überhaupt einen ausreichenden Bewegungsraum zur Deckung eines **angenommenen** 14-bp-Roundtrip-Kostenbudgets hat. MFE/MAE sind keine realisierten PnLs: beide Extremwerte können innerhalb derselben OHLC-Kerze auftreten, und ihre Reihenfolge ist aus 5-Minuten-Daten unbekannt.

**Mechanismus:** Trend-Pullbacks versuchen Anschluss an die übergeordnete Richtung, Breakouts an Preisfindung nach Range-Verlassen, Reversion an Übertreibungsabbau. Das sind nur Vermutungen, keine nachgewiesenen Marktgesetze.

**Originaldaten:** 16 monatliche BTCUSDT Binance Futures 5m Parquet-Dateien, 2024-09 bis 2025-12. Originaler R12-Datenvalidator wird wiederverwendet, Dateien bleiben read-only. Die originale R12-Regeldatei muss unter `studies/R12_3_Strategien_BTC_Explorativ.py` vorhanden sein und SHA256 `7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d` besitzen. Keine separaten Datenkopien nötig. **2024 und 2025 sind früher untersucht, kein Blindtest**.

**Einstiege:** Alle gültigen R12-Signale nach Kerzenschluss `j`; Auswertung zum `open[j+1]`. Anders als R12-Simulator: **kein** Ausschluss während offener Positionen, um die reine Signalqualität und Signalhäufigkeit getrennt von Positionsmanagement zu messen. Dadurch können Signal-Folgeverläufe stark überlappen. Keine implizite simultane Handelbarkeit!

**Beobachtungshorizonte:** Vier *vorab* fixierte Beobachtungsfenster: 3, 6, 12, 24 volle 5m-Kerzen (15/30/60/120 Minuten). Fester hypothetischer Exit bei `open[j+1+h]`, nicht am Signal-Kerzenclose und ohne TP-/Stop-Optimierung. Alle Auswertungen basieren auf derselben Signalpopulation mit verfügbarem vollem 120m-Fenster. Jeder Jahresabschnitt warmup 300 Kerzen, kein Ziel oder Einstieg über Partitionsgrenzen hinweg.

**Kontrollen:** Zu jedem Signal eine mit fester RNG/Seed gewählte Kerze **ohne dasselbe Signal**, zuerst im gleichen UTC-Kalendertag und gleichen Stundenfenster, sonst nur gleicher Tag. Gleiche Long/Short-Richtung wie das eigentliche Signal. Ziehung mit Zurücklegen, ohne Verwendung künftiger Kursausgänge bei der Auswahl. Dokumentiere `same_day_hour`, `same_day_fallback`, `unmatched`. Kontrollpunkte sind nicht notwendigerweise unabhängige Events, und die Kontrollgruppen unterscheiden sich per Konstruktion im Signalstatus. Dies begrenzt kausale Interpretierbarkeit.

**Auswertungen:** Anzahl aller Signale je Tag und nach Seite, MFE- und MAE-Median und 75%-Quantil in bp, Bruttorendite nach jeweiligem Horizont, fiktive feste Exit-Rendite minus **14 bp Modellkosten** (R12-Gebühr/Slippage/Funding-Reserve; historische Funding-Abrechnung und Orderbuch nicht vorhanden), Referenzrendite, mittlere Differenz Signal minus Kontrolle und ein **deskriptives**, gepaartes 7-Kalendertage-Blockbootstrap-Konfidenzintervall über kalenderabhängige Ereignissummen/-anzahlen. Vorperiodische 60-Minuten-Richtung `C[j]/C[j-12]-1` nur zur *beschreibenden* Signalausrichtung; keine automatische Trendauswahl aus den Ergebnissen. Keine Schätzung aus OHLC, ob MFE vor MAE eintritt.

## Phase B: Fehlerschutz und Freigabebedingungen

- Eingefrorenes R12-Signalmodul per SHA256 prüfen; nicht erneut R12-PnL backtesten und keine Handelsregeln abändern.
- Datengate: Exchange/Instrument/Preisquelle, alle vollständigen Monatsdaten, Zeitzonen, eindeutige UTC-Zeitstempel, OHLC-Plausibilität und geschlossene Kerzen über R12-Validator.
- Synthetic-Tests: Long/Short MFE/MAE, abgeschnittenes Zukunftsfenster beeinflusst frühere Messung nicht, fester Exit `open` *nach* vollständigen Beobachtungsbars, nur dokumentiertes hypothetisches Kostenbudget.
- In jedem Zeitabschnitt werden Signalindex, Entryindex, Maximalbeobachtungsfenster und Kontrollindex begrenzt; keine Grenzübertritte. Start mit `--preflight`, danach einmalig `--run`; bereits existierender Ergebnisordner stoppt statt Überschreiben.
- Der abgeschlossene Datensatz ist bereits durch R8-R12 explorativ bekannt. Keine konfirmatorische Aussage über eine profitable Strategie, keine p-Werte als Bestätigung, keine Gewinnerselektion als Beweis.
- Ergebnisarchiv ausschließlich unter `~/QuantResearch/R13_BTC_EntryPaths/Sep2024_Dec2025_v1/` mit `R13_RESULTS.json`, `R13_ENTRY_PATHS.csv`, `R13_REPORT.md`.

## Methodische Einordnung

Diese Analyse **beobachtet** Eintrittssignale und Preisexkursionen. Ein großer MFE-Wert ist kein handelbarer Gewinn, denn der vorherige MAE-Verlauf und die Intrabar-Reihenfolge sind unbekannt. Die differenzierte Entscheidung für Stop, TP, Zeitfenster und realistische Gebühren einschließlich tatsächlich angefallener Funding-Zahlungen ist eine **separate, prospektiv zu spezifizierende** Untersuchung. Die zuvor verwendeten Daten dürfen nicht nachträglich zu einem Blindtest erklärt werden.
