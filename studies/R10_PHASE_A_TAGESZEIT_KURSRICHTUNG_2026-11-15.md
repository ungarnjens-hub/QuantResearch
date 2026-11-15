# R10 – Tageszeitabhängige Kursrichtung bei BTC und ETH
**Phase A: Forschungsdesign, 15.11.2026**  
**Status:** Vorregistrierung eines *explorativen* Marktverhaltensatlas. Keine Messung, keine Backtest-Strategie, keine Freigabe für Phase C.

## Ziel
Feststellen, ob es in den Binance-USD-M-Perpetual-Futures auf BTC und ETH **wiederkehrende UTC-Stunden mit systematisch positiver oder negativer Rendite** gibt, die sich zwischen September–Dezember 2024 und Januar–Dezember 2025 ähnlich verhalten. Eine wiederkehrende größere Bewegungsstärke ist **kein** Richtungsbefund.

## Fachgrundlage und vermuteter Mechanismus
- Die empirische Literatur dokumentiert stundenabhängige Krypto-Renditen und deutliche Tagesmuster; ihre Stabilität kann geringer sein als bei Volatilität und Aktivität: `https://doi.org/10.1007/s11156-024-01304-1`.
- Die Studie *Turn-of-the-candle effect in bitcoin returns* untersucht eine zeitlich feinere Minuten-Anomalie, nicht unsere 60-Minuten-Stundenrenditen: `https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/`. Ein Literaturbefund ist kein Nachweis für unsere Datenperiode.
- Potenzieller Mechanismus: wiederkehrende institutionelle Handelsaktivität, regionaler Liquiditätsbedarf und planmäßige Marktübergänge. **Keine Vorannahme**, dass die Uhrzeit allein vorhersagbar ist. US-/EU-Sommerzeit kann starre UTC-Hours verwischen; die erste Analyse verwendet deshalb nur UTC und dokumentiert DST als Beschränkung.

## Fixierte Fragestellung und Hypothesen
**H0:** Die erwartete nachfolgende 60-Minuten-Logrendite hängt nicht systematisch von der UTC-Startstunde ab, nachdem allgemeine Marktdrift bzw. das jeweilige Teiljahr berücksichtigt ist.  
**H1:** Mindestens eine UTC-Startstunde weist eine stabile, positive oder negative Abweichung auf. Die 24 Stunden sind eine *vorab deklarierte* Kandidatenfamilie, nicht 24 unabhängige bestätigte Entdeckungen.

## Märkte und Daten
- BTC/USDT:USDT und ETH/USDT:USDT, Binance USD-M linear Perpetual Futures, `last_trade`, `/fapi/v1/klines`, 5-Minuten-OHLCV, nur abgeschlossene Bars.
- Datenquellen: 32 unveränderte monatliche Parquet-Dateien, `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/{BTC_USDT,ETH_USDT}/5m/`, Zeitraum **2024-09-01 00:00 UTC bis 2026-01-01 00:00 UTC exklusiv**, jeweils 140.256 Kerzen, Datencheck zuvor bestanden.
- Schema: `open_time`, `close_time`, `close`, `is_closed`, `exchange`, `market_type`, `contract_type`, `timeframe`, `price_source`, `source_endpoint`; Decimal-Kurse nur nach endlicher, positiver Kontrolle in Double umrechnen. Dateihashes, Programmversionen und vollständigen Datenverbrauch registrieren.
- September–Dezember 2024 und Januar–Dezember 2025 getrennt ausweisen. **Beide Abschnitte sind explorativ**: frühere Forschungszugriffe, insbesondere auf 2025, verbieten die Bezeichnung als frischer Blindtest.

## Ereignis und Messzeitpunkt
- Für jede vollständige UTC-Stunde `h` eines Kalendertages berechnen wir **eine** 60-Minuten-Logrendite:  
  `r(d,h) = ln(C_last_bar(d,h+60m)/C_last_bar(d,h))`, wobei `C_last_bar(d,h)` der Schlusskurs der um 5 Minuten vor Stundenbeginn geöffneten Kerze ist, deren Schluss exakt auf den Stundenbeginn fällt. Beispiel 14:00–15:00 UTC: Close der Kerze 13:55–14:00 versus Close der Kerze 14:55–15:00.
- **Wichtige Startgrenze:** 2024-09-01 00:00 UTC benötigt den Schlusskurs der 2024-08-31 23:55-Kerze. Dieser ist zwar im August-Bestand vorhanden, muss aber als exakt gültiger vorheriger Schluss nachgewiesen werden. Falls er nicht vorliegt, wird **nur diese erste Stunde** bei beiden Märkten aus der Auswertung ausgeschlossen und ausdrücklich protokolliert. Für die restlichen Stundenpaare liegen die benötigten Schlusskurse innerhalb des vollständigen Untersuchungsfensters.
- Es wird **kein Handel zum bereits beobachteten Schlusskurs** simuliert; ein handelbarer Einstieg braucht später eigene Ausführungsdaten/Annahmen. Kein neues Signal benötigt den zukünftigen Schlusskurs als Feature.

## Primäre deskriptive Größen (24 Stunden x 2 Märkte)
1. Mittlere 60-Minuten-Logrendite in **Basispunkten**, jeweils je Jahr und gepoolt; Stichprobenzahl und Zahl vollständiger Tage.
2. Richtung: Quote `r>0`, `r<0`, `r=0` separat; Trefferquote `r>0` nur unter `r!=0` mit ausgewiesenem Nenner.
3. Stundenbezogener Renditeunterschied zur durchschnittlichen Stundenrendite desselben Jahres; damit der BTC/ETH-Aufwärtstrend nicht als angebliche Uhrzeit-Anomalie gilt.
4. Ergänzend Median, 10./90. Perzentil der Renditen und Anzahl positiver/negativer Monate (keine neue Schwellenentscheidung daraus ableiten).

## Statistik und Mehrfachtests
- Tagesweise *gepaarte* kreisförmige Moving-Block-Bootstrap-Resamples aus **7 aufeinanderfolgenden UTC-Tagen**, **5.000** Ziehungen, Seed **20261115**, für alle 24 Stunden gemeinsam. 95%-Perzentilintervalle **nur beschreibend**, solange Kalibrierung nicht separat nachgewiesen wurde.
- Keine nachträgliche Wahl der „besten Stunde“ als Signifikanzbeweis. Für eventuelle confirmatorische Folgeprüfung: 24-Hours x 2-Assets-Familie und entsprechende Multiplikitätskontrolle bzw. Max-Statistik-Test vorab kalibrieren. Jetzt **keine** p-Werte und keine Behauptung einer statistisch bestätigten Handelschance.
- Ein Kandidat darf *nur für spätere, neu vorregistrierte Prüfung* nominiert werden, wenn das Vorzeichen in beiden Abschnitten übereinstimmt, kein einzelner Monat den Pooled-Effekt allein trägt, wenigstens 100 Kalendertage je Abschnitt nach Datenprüfung verfügbar sind, und die Größenordnung plausibel über den später zu messenden Handelskosten liegt. Bei Nichteinhaltung: **keine robuste Kandidatennominierung**. Diese Kriterien erzeugen keine Blindtest-Bestätigung.

## Negative Kontrollen und ökonomische Grenze
- Unbedingte Gesamtrendite und Jahresdrift als Baselines; Wochenend-/Wochentag-Aufschlüsselung **nur explorative Diagnose**, nicht zusätzliche unregistrierte Candidate-Suche.
- 60-Minuten-Brutto-Logrenditen sind *keine* Freqtrade-Strategie und keine Netto-PnL-Reihe. Vor jedweder Profitabilitätsaussage separat: tatsächlicher Einstieg nach Information, Exit, bid/ask, Taker/Maker-Gebühren, Slippage, Funding, Haltedauer, Drawdown und Execution-Fehler, mit unabhängigen Daten.

## Ausführungsbedingungen und Stop
- **Phase B vor Phase C:** Zeitstempel/Schlusskursreferenz, lückenloses Stundenraster, Datei-Hashes, Bootstrap-Zuordnung und künstliche Null-/Known-Effect-Prüfungen kontrollieren; keine stillen Korrekturen nach Resultaten.
- Ausschließlich isoliertes Forschungsverzeichnis. Original-Parquets und TradingLab/Freqtrade-Paper-Bots niemals verändern.
- Phase C erst mit gesonderter Freigabe. Das Ziel ist *ein Marktverhaltensatlas*, keine „Stunden-Strategie“.

## Quellen
- `https://doi.org/10.1007/s11156-024-01304-1`
- `https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/` (andere Minutenebene; nur Abgrenzung)
