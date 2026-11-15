# R10-V2 – BTC: Wann folgt auf einen Impuls Fortsetzung oder Gegenbewegung?
**Phase A – Forschungsdesign | 15.11.2026 | Version 1.0 | NO MARKET MEASUREMENT**

## 0. Abgrenzung und Änderungsregister
Dieses Dokument ersetzt die **Fragestellung** aus `R10_PHASE_A_TAGESZEIT_KURSRICHTUNG_2026-11-15.md` (Git-Commit `46fc129`), ohne diese Datei zu verändern. Grund: Nutzerziel ist eine **BTC-spezifische Marktsituation**, aus der erst später eine wirtschaftlich ausführbare Handelsregel entwickelt werden könnte, nicht ein BTC/ETH-Vergleich und nicht die bloße Wahrscheinlichkeit positiver Stundenrenditen. R9-Schwellen oder Ergebnisse werden nicht als Beleg für R10-V2 interpretiert. Die Studie ist ein **neues, ausdrücklich exploratives** Forschungsdesign.

## 1. Mechanismus und Literatur
Nach außergewöhnlich starken BTC-Kursimpulsen sind sowohl **Trendfortsetzung** (z. B. schrittweise Preisfindung/Liquiditätsnachfrage) als auch **Gegenbewegung** (z. B. Überreaktion/Liquiditätsbereitstellung) plausibel. Die Literatur berichtet beide Effekte, teilweise abhängig von Marktbedingungen. Keine der Quellen belegt die unten gewählte spezielle Parametrisierung:
- Wen, Bouri, Xu & Zhao (2022), *Intraday return predictability in the cryptocurrency markets: Momentum, reversal, or both*, DOI `10.1016/j.najef.2022.101733`.
- Shen, Urquhart & Wang (2022), *Bitcoin intraday time series momentum*, DOI `10.1111/fire.12290`.
- De Nicola (2021), *On the Intraday Behavior of Bitcoin*, DOI `10.5195/ledger.2021.213`.

## 2. Eine konkrete und falsifizierbare Forschungsfrage
**Unterscheidet sich die nachfolgende 30-Minuten-Rendite in Impulsrichtung nach starken BTC-Impulsen abhängig davon, ob die vorausgehende 2-Stunden-Bewegung in dieselbe Richtung oder entgegengesetzt verlief?**

**Primäre Hypothese H1 (gerichtet):** Die durchschnittliche signierte 30-Minuten-Folgerendite ist bei *trendkonformen* starken Impulsen **höher** als bei *trendgegenläufigen* starken Impulsen. Null H0: Differenz <= 0. Dies ist eine begründete, aber unbestätigte Arbeitshypothese. Negative Mittelwerte je Gruppe deuten auf Gegenbewegung, positive auf Fortsetzung. H1 kann auch bei zwei negativen Mittelwerten bestehen; dies ist dann **kein Nachweis handelbarer Trendfortsetzung**.

Keine Zusatzhypothese zu 24 Tageszeiten, kein Volumenfilter, keine ETH/SOL-Tests, keine Auswahl des besten 5m/15m/30m-Horizonts.

## 3. Daten und Zeitaufteilung
- Börse: Binance USD-M Futures; BTCUSDT linearer Perpetual; `last_trade`-OHLCV; 5-Minuten-Kerzen.
- Originalpfad ausschließlich **lesen**: `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m/`.
- Gemeinsamer geprüfter Bestand: **01.09.2024 00:00 UTC bis 01.01.2026 00:00 UTC (exklusiv), 140.256 Kerzen**. Korrekte Preis-/Volumenspalten: `close`, `volume_base` (Volumen wird für R10-V2 nicht als Feature benutzt). `open_time` bezeichnet den Start, nicht den Abschluss; bar-Schlusszeit für die Entscheidung = `open_time+5min`. `close_time` endet i. d. R. 1 ms davor.
- **September–Dezember 2024: explorative Entdeckung; Januar–Dezember 2025: zeitliche Stabilitätsanalyse, NICHT unabhängiger Blindtest**, weil historische Daten bereits in anderen Forschungsprojekten genutzt wurden.
- Keine Wiederverwendung von R7-/R8-B-reservierten zukünftigen Testperioden. Ein unabhängiger Bestätigungstest würde später getrennt registriert.

## 4. Exakte, vor der Messung einzufrierende Ereignisdefinition
Zeitindex `j` = letzter **vollständig abgeschlossener** 5-Minuten-Kerzen-Schlusskurs `C_j`. Chronologisch vollständige Kurse und 5-Minuten-Renditen `r_i=ln(C_i/C_{i-1})`.

1. **Impuls:** `I_j=ln(C_j/C_{j-6})` über exakt sechs abgeschlossene 5m-Kerzen (=30 Minuten).
2. **Historische Volatilitätsreferenz:** `s_j=std(r_{j-293},...,r_{j-6})` mit Stichproben-SD (`ddof=1`); genau **288 Renditen, vollständig VOR dem Impuls**. Null/nichtendliche SD: keine Beobachtung.
3. **Starker Impuls:** `|I_j|/(sqrt(6)*s_j) >= 2.0`; `I_j=0` ausgeschlossen. Dies ist ein explorativer, fixierter Schwellenwert, nicht aus Marktergebnissen optimiert.
4. **Vorlaufender Trend:** `T_j=ln(C_{j-6}/C_{j-30})`, genau zwei Stunden, deren letzte Kerze VOR dem Impuls endet. `sign(T_j)==sign(I_j)` => `trendkonform`; `sign(T_j)!=sign(I_j)` => `trendgegenläufig`; `T_j=0` => transparent ausgeschlossen. Keine sich überschneidenden Kursabschnitte der beiden Merkmale.
5. **Zielgröße:** `Y_j=sign(I_j)*ln(C_{j+6}/C_j)` für die nächsten 30 Minuten. Bericht in Basispunkten `10_000*Y_j`: positiv = Fortsetzung, negativ = Gegenbewegung.
6. **Beobachtungs-/Ereignissperre:** Ereignisse werden chronologisch nach vollständig geprüftem Signal erkannt, unabhängig von der Gruppe. Nach einem Ereignis bei `j` sind weitere Entscheidungen an `j+1,...,j+6` ausgeschlossen. Gemeinsame Sperre für beide Gruppen. Keine Ereignisse mit Labels außerhalb des vorregistrierten jeweiligen Zeitabschnitts; keine Neubewertung, um Gruppenzahlen zu erhöhen.
7. **Zwei Richtungen:** Aufwärts-/Abwärtsimpulse werden für das signierte **primäre** Outcome zusammengefasst; Long/Short-Anteile werden deskriptiv protokolliert. Keine Suche nach der besten Richtung.
8. **Kein Handelsentry:** `C_j` ist zum Prognosezeitpunkt erst gerade bekannt. Ein realer Einstieg könnte nicht rückwirkend zu `C_j` garantiert werden. Dies ist **kein PnL oder handelbarer Backtest**.

Indexbeachtung: Voraussetzung sind `j>=294` sowie `j+6<len(C)` innerhalb des jeweils begrenzten Untersuchungsabschnitts. Zeitabschnitt 2025 bekommt optional historische, *vorab nur zur Merkmalsbildung* verfügbare Warm-up-Kerzen aus Ende 2024; keine Labels vor Jan. 2025 und keine Ereignissperre über die Jahresgrenze hinweg ohne explizite Implementierungsregel. Diese technische Frage ist in Phase B verbindlich zu fixieren.

## 5. Primäre Metrik, Kontrollen und Entscheidungskriterien
- **Primär:** `Delta=mean(Y|trendkonform)-mean(Y|trendgegenläufig)` in bp je zeitlichem Teilabschnitt und gepoolt (ein BTC-Markt, eine registrierte Kontrastfamilie). Pro Gruppe zusätzlich Mittelwert, Median, Anteil `Y>0`, Streuung, Event- und Tageszahlen, impulsgerichteter 30m-Renditeverlauf.
- **Baselines:** Null-Folgerendite (`Y=0`) als Richtungslosigkeit; Gesamtheit aller starken Impulse (ohne Vortrend-Split). Gleiche bereits ausgewählte Ereignismenge, keine unfaire Stichprobe.
- **Mindestdeskription:** vorläufig 40 Ereignisse je Gruppe sowie 20 unterschiedliche UTC-Tage je Gruppe; darunter ausschließlich „unzureichende Stichprobe“ und kein positives/negatives Urteil. Bei ausreichend Beobachtungen bleiben KIs wegen methodischer Besonderheiten zunächst **deskriptiv**.
- **Abhängigkeit:** tägliche Paare von Ereignisaggregaten, 7 zusammenhängende UTC-Tage per gepaartem Moving-Blockbootstrap; 5.000 Ziehungen, Seed 20261115. Den konkreten Resampling- und Boundary-Algorithmus in Phase B gegen synthetische Null-/Alternativ- und Regimeprozesse prüfen, **bevor** ein p-Wert oder eine Signifikanzfreigabe möglich wird.
- **Erfolg als Forschungsbefund, nicht Trading-Erfolg:** Stabile Vorzeichen/Größenordnung 2024 und 2025, positive *relevante* Differenz und Unsicherheit. Ein festes wirtschaftliches Mindestniveau wird erst in Phase B nach nachvollziehbarem Ausführungskosten-Szenario **vor echten Ergebnissen** fixiert. Keine nachträgliche „beste Stunde“, Richtung, Zeitspanne oder Schwelle.
- **Scheitern/ungeklärt:** Kleine, instabile oder breit unsichere Effekte => nicht bestätigt/ungeklärt. Negative Ergebnisse vollständig berichten; keine Parametertests als versteckte Fortsetzung.

## 6. Verbindliche Schritte
- **A:** Dieses Design archivieren und versionieren.
- **B:** Prüfen: tatsächliche Datenmetadaten, Files/SHA, keine Zukunftsdaten, Indexgrenzen, Warm-up, Nullimpulse, Kalender-/Regimeblockbootstrap und Selektionsbias. Zusätzlich die finanzökonomische Schwelle und den Datenverbrauch fixieren; Synthetik-E2E mit bekanntem Null- und Alternativfall. *Keine realen Event-/Renditemessungen.*
- **C:** Nur einmalige explorative Messung nach ausdrücklicher Freigabe; Ergebnisdateien isoliert unter `~/QuantResearch/R10_Explorativ/`, kein Touch produktiver Bots/Originale.
- **D:** Gegen Baselines, Phasenstabilität und Unsicherheit interpretieren. Wenn interessant, **separates neues Design** einer frühestens nach Kerzenschluss ausführbaren Handelsregel inklusive Gebühren, Spread, Slippage, Funding, Kapitaleinsatz und Stop-Regeln.
- **E/F:** Unberührte Daten nur nach vorher fixierter Bestätigungsentscheidung, Ergebnisse registrieren und archivieren.

## 7. Status
**Phase A: erstellt. Phase B: offen. Phase C: nicht freigegeben.**
Weder Marktvorhersagen noch Ergebnisoptimierung, Live-/Paper-Trades oder produktive Änderungen werden durch dieses Protokoll autorisiert.
