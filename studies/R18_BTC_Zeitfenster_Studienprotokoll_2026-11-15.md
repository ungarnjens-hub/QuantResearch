# R18: BTC-Bewegungsintensität nach Tageszeit und Wochentag

**Phase A/B, vor der Marktauswertung eingefroren. Explorative Marktforschung, keinerlei Orders oder Trading-Strategie.**

## Wissenschaftliche Grundlage

- Brauneis, Mestel & Theissen (2025), *The crypto world trades at tea time*, Review of Quantitative Finance and Accounting, doi:10.1007/s11156-024-01304-1. Dokumentiert tageszeitliche Muster bei Volatilität, Liquidität und Handelsvolumen für viele Kryptopaare.
- Aldhahi (2026), *Bitcoin on Wall Street Time*, Journal of Risk and Financial Management, doi:10.3390/jrfm19090707. Dokumentiert Zusammenhang des BTC-Volatilitätsmusters mit NY-Handelszeiten und US-Sommerzeit.
- *The Role of Binance in Bitcoin Volatility Transmission* (2022), Applied Economics Letters, doi:10.1080/1350486X.2022.2125885. Intraday-Muster von BTC an Binance, inklusive US-Handelsstart.

## Fragestellung und Hypothesen

H1 (deskriptiv falsifizierbar): BTC-Futures zeigen keine gleichförmige Verteilung der realisierten intraday Bewegungsgröße über die 24 UTC-Stunden. H0: Keine messbaren Unterschiede der stündlichen Verteilungen; H1 wird nur explorativ bewertet, keine formale Entscheidung bei 24 parallelen Zeitfenstern.

H2: Die NYSE-Öffnungsstunde 09:30–10:30 America/New_York unterscheidet sich im beobachteten BTC-Stundenrange von 08:30–09:30 und von 10:30–11:30, 11:30–12:30. Gepaart nach lokalem Kalendertag, kein Post-hoc-Verschieben des Fensters. Weekends als Placebo; US-Börsenfeiertage nicht aus dem Mo-Fr-Muster entfernt, deshalb ist „Börsenstart“ nur die lokale Uhrzeit, kein Nachweis der kausalen NYSE-Session.

H3 (deskriptiv): Wochentag und UTC-Stunde haben eine unterschiedliche Bewegungshäufigkeit. Woche × Stunde ist ein explorativer 7×24-Heatmap-Vergleich; keine Gewinner-Zeitfenster aus denselben Daten bestätigen.

## Daten und Messgrößen

BTC/USDT Binance linear perpetual, last-trade Futures 5m OHLCV, exakt 16 vorhandene Monatsdateien Sept 2024 bis Dez 2025, 140.256 vollständige, geschlossene Kerzen. Zuvor geprüfter und per SHA256 fixierter R12-Datenloader als reine Lesefunktion. Kein Daten-Download, keine Änderungen am TradingLab oder Paper-Bots.

- Pro vollständiger UTC-Stunde (12×5m): High/Low-Range in Basispunkten, absoluter Open/Close-Ertrag, Summe der 5m-Quadratlogrenditen (*realized variance*), Median/75./90. Perzentil, P(Range>=30 bp), Handelsvolumen (nur diagnostisch).
- 30 bp ist fest vorab gesetzte deskriptive Schwelle für Bewegungspotenzial; keine Aussage, dass 30 bp handelbar sind oder Kosten decken.
- BTC-Volatilität ändert sich zwischen Jahren und Marktphasen; daher zusätzlich prozentualer Tagesanteil an der realisierten Varianz.
- R18 trennt Sept–Dez 2024 strikt von Jan–Dez 2025; beides ist nach früheren Experimenten bereits bekannt, kein Blindtest.
- NY-Zeitfenster lokal 08:30, 09:30, 10:30, 11:30 Uhr für jeweils volle 60 Minuten. US-Sommerzeit automatisch durch `America/New_York`, niemals fixes UTC-Offset. Weekdays und weekends getrennt.

## Methodenaudit, Sperren und Entscheidung

1. Alle 5m-Zeiten strikt auf UTC-Raster, gleichmäßig, keine Lücken oder Dubletten, Preise und OHLC plausibel; Monatshashes protokollieren.
2. Zeitfenster werden ausschließlich nach Bar-Start gruppiert; Ergebnisse sind **nachträglich realisierte Bewegungen**, keine Features vor einer hypothetischen Order. Kein Look-ahead-Claim.
3. Ungewöhnliche Tage nicht entfernen und NYSE-Feiertage nicht stillschweigend als Handelstage klassifizieren.
4. Stunden-Ranges und RV enthalten unterschiedliche Informationen. Realisierte Volatilität/Ranges ergeben **keine** Vorhersage für die Richtung. Eine hohe 60m-Range bedeutet nicht, dass sich die gesamte Strecke verdienen ließe.
5. 24 UTC-Stunden, sieben Wochentage und vier NY-Stunden sind viele Vergleiche. Ergebnisse nur beschreibend; Rankings sind explorativ. Keine einseitigen Signifikanzclaims ohne kalibriertes Multiplicity-Konzept.
6. Ergebnisse der Perioden vergleichen, nicht nur gepoolten Durchschnitt. Für robusten Nachweis separate neue Stichprobe erforderlich.
7. Nur bei wiederkehrend größerer beobachteter Bewegung eine **neue** spezifische Entry-Hypothese erarbeiten, nicht historische Richtungen/Stop-Parameter aus R18 optimieren.
8. Preflight ausschließlich synthetische DST- und Zeitindexprüfungen plus Originaldatengate; Lauf nur nach Commit, nie doppelt auf denselben Ergebnisordner.

**Erwartete Evidenz:** kompletter UTC-Stunden- und Wochentagsvergleich, 7×24-Heatmap-Daten, NY-open / +1h / +2h relativ zu vorheriger Stunde, mit Realized-Range-/RV-Messung, ohne eine profitable Handelsstrategie vorzutäuschen.
