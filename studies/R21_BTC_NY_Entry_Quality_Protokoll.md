# R21: BTC NY-Opening-Range, Qualität der Einstiegssignale

Datum 2026-11-15. Phase A/B: deskriptiver Audit der bereits abgeschlossenen R20-Simulation. **Keine neue Strategie, keine Optimierung, kein Blindtest.**

## Fragestellung

Haben R20-Ausbrüche, die später ihr 1,5R-Ziel erreichen, schon vor dem Einstieg systematisch andere Markteigenschaften als Ausbrüche, die zuerst am Stop scheitern? Die R20-Einstiege und deren Outcomes bleiben unverändert. Die Untersuchung ist **explorativ**, das Label Ziel/Stop dient ausschließlich als *nachträgliche Gruppierung*, niemals zur Auswahl eines historischen Trades.

## Daten und Ausführung

- Quelle: R20_TRADES.csv und R20_RESULTS.json unter `~/QuantResearch/R20_BTC_ORB_5m_15m/Sep2024_Dec2025_v1`.
- Exakt identischer, SHA256-fixierter R19-Ausführungscode und über diesen verifizierter R12-Datenloader. 16 originale BTC-USDT-5m-Parquet-Dateien Binance Futures, read-only.
- Code- und R20-Ergebnis-Hashes vor dem Lauf vergleichen; in R20 gespeicherte Zahlen pro Zeitraum/Variante exakt aus CSV nachrechnen. Stop bei fehlender Übereinstimmung.
- Kein Umschreiben vorhandener Studien, Profile, Paper-Bots oder Originaldaten. Ausschließlich neues Verzeichnis `~/QuantResearch/R21_BTC_NY_EntryQuality/Sep2024_Dec2025_v1`, kein Überschreiben.
- Zwei ursprüngliche Varianten ORB_5m und ORB_15m, jeweils 2024 Sep–Dez und 2025 Jan–Dez getrennt. Ein Trade/NY-Tag/Variante.

## Exakt begrenzte Merkmale (alle vor Entry verfügbar)

Berechnet zum Abschluss der Signalkerze j, nicht nach Trade-Ausgang:

1. ATR(14) in Basispunkten relativ zum Signal-Schlusskurs.
2. Vorherige Stunde: richtungsbereinigte Kursrendite über 12 5m-Schlusskurse, Basispunkte.
3. Körpergröße der Signalkerze geteilt durch ATR(14).
4. Close-Überschreitung der Opening-Range-Grenze in Signalrichtung / ATR(14).
5. Breite der Opening Range / ATR(14).
6. Geschätzte Stopdistanz Signal-Close zur Range-Mitte in Basispunkten, keine Kenntnis des künftigen Entry-Open.
7. Minuten vom 09:30-NY-Start bis zum Abschluss des Ausbruchssignals.

Ziel-, Stop- und Zeit-Exits werden allein aus unveränderten R20-Trades gelesen. Ausgabe: n pro Outcome und Median der sieben Merkmale je Ziel/Stop sowie Gesamtmedian. Keine nachträgliche Schwellenwahl, kein Filter-Backtest, keine Signifikanz- oder Profitabilitätsbehauptung.

## Entscheidungen und Grenzen

- Existiert für ein Merkmal ein deskriptiver Unterschied gleicher Richtung in beiden Jahresabschnitten, ist er **nur eine mögliche Hypothese**. Ein späteres separates Studienprotokoll darf genau eine theoretisch begründete Hypothese auswählen, muss aber ausdrücklich die vorherige Dateninspektion registrieren.
- Ohne auf noch nicht untersuchten Daten bestätigten Netto-Erwartungswert keine Einführung einer Handelsregel.
- Trade-Outcomes basieren auf 5m-OHLC mit konservativem Stop bei Same-Bar-Mehrdeutigkeit, Kosten 14bp/24bp nur Modellannahmen, kein echtes Orderbuch und kein tatsächlich abgerechnetes Funding.
- Die Auswahl des NY-Fensters ist bereits datengetrieben (R18). Historie 2024/2025 mehrfach untersucht: strikt kein unabhängiger Holdout.
