# R20 BTC NY-Opening-Range: 5 Minuten gegenüber 15 Minuten

**Datum:** 2026-11-15. **Status:** Vorab-Forschungsdesign und Methodenaudit; keine realen R20-Marktergebnisse vor Freigabe. **Ausschließlich isolierte Marktforschung.**

## A. Fragestellung und Mechanismus

Die US-Aktieneröffnung 09:30 America/New_York war im zuvor explorierten BTC-Datensatz ein Fenster hoher Bewegung (R18). R19 verwendete die Spanne 09:30–09:45 NY aus drei abgeschlossenen 5m-Kerzen, danach den ersten abgeschlossenen 5m-Schluss außerhalb dieser Spanne. Diese Regel war nach modellierten Kosten 2024 und 2025 negativ. Eine 5m-Opening-Range könnte einen frühen Impuls bereits nach der ersten abgeschlossenen 5m-Kerze erkennen, könnte zugleich aber häufiger Fehlausbrüche und engere Stops produzieren.

**H1 (einzige primäre Hypothese):** Die exakt definierte 5m-Opening-Range-Ausbruchsregel erzielt im nachfolgenden historischen Fenster einen höheren durchschnittlichen **modellierten Netto-Basispunktertrag je NY-Handelstag** als die eingefrorene 15m-R19-Regel. **Nullhypothese:** Differenz <= 0. Die Antwort wird in beiden Zeitabschnitten 2024_SepDec und 2025_JanDec deskriptiv getrennt berichtet. **Keine Bestätigungsansprüche:** beide Zeitabschnitte und das NY-Zeitfenster sind bereits exploriert.

Sekundär, ohne Auswahl/Optimierung: Richtung des Gewinns/Verlustes je Trade, Anzahl Trades, Profit-Faktor, Stop-/Target-/Zeitexit, Stop-Distanz (bp), Kostenstress, tägliche Differenz mit deskriptivem 7-Tage-Blockbootstrap. Es gibt **keine** nachträgliche Auswahl der besten Stunden oder Märkte.

Wissenschaftliche Grundlage: Opening-Range-Breakout als explizite Handelsregel, z. B. Holmberg, Lönnbark & Lundström (2013), *Finance Research Letters* 10(1), 27–33, DOI 10.1016/j.frl.2012.09.001; Tsai et al. (2019), *IEEE Access*, DOI 10.1109/ACCESS.2019.2899177. Die genannten Studien untersuchen **andere** Märkte/Perioden und sind kein BTC-Nachweis. Blockbootstrap adressiert zeitliche Abhängigkeit nur näherungsweise; hier rein deskriptiv, nicht mehrfachtestkalibriert.

## B. Eingefrorene Regeln

- **Markt/Daten:** BTC/USDT linear Binance Perpetual, 5m, ausschließlich `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m/`, **nur lesend**; 16 originale monatliche Dateien, 2024-09 bis 2025-12; Hash-/Qualitätsaudit via eingefrorene R12-Ladefunktion in R19. Keine System-/Paper-Bot-Änderungen.
- **Handelstage:** Identische NY-Wochentage/Datumsmengen wie R19 (87 in 2024 Sep–Dez; 261 in 2025); US-Aktienfeiertage sind in dieser Baseline *nicht* entfernt. New-York-Sommerzeit via `zoneinfo`.
- **5m-Opening-Range:** Hoch/Tief der *ersten vollständig abgeschlossenen* 5m-Kerze 09:30–09:35 NY. Ab der nächsten Kerze (09:35–09:40) bis Signal-Kerze 11:25–11:30 NY: **erster** vollständig abgeschlossener 5m-Schluss **außerhalb** dieser historischen Range, Long über Hoch oder Short unter Tief. Falls keine Signal-Kerze: kein Trade. Einstieg Eröffnung der folgenden 5m-Kerze.
- **15m-Opening-Range:** **Keine Neuimplementierung der Baseline.** Die unveränderte R19-Funktion `events` erzeugt ORB auf der 09:30–09:45-Spanne und den nachfolgenden Signal-Kerzen. Ergebnisse müssen mit existierendem `R19_RESULTS.json` exakt übereinstimmen (Trade-Zahl und durchschnittlicher Nettoertrag, je Zeitabschnitt), sonst Abbruch.
- **Beide Varianten:** Ein Trade pro Variante und NY-Tag, Stop in der Mitte **der jeweiligen Opening-Range**, Ziel 1,5 × anfängliche Stop-Distanz, maximal 24 abgeschlossene 5m-Kerzen = 120 Minuten. Einstieg nur bei positivem richtungsbezogenem Stop-Abstand. Unklare SL/TP-Berührung innerhalb einer Kerze -> Stop zuerst. Kurslücke gegen die Position zum schlechteren Open. Basiskosten 14 bp Roundtrip und Stress 24 bp Roundtrip (inklusive pauschaler Fundingreserve, keine nachgewiesenen echten Fundingzahlungen).
- **Vergleich:** Parallel nur in *zwei hypothetischen separaten* Modellläufen. Tagesnetto pro NY-Handelstag; nicht gehandelte Tage gehen mit **0 bp** in beide Vergleichsspalten ein. 5m minus 15m täglich gepaart. 7-Tage-Blockbootstrap mit 2.000 Wiederholungen, festem Seed. Keine Portfolio-/Hedge-Interpretation.
- **Hauptmaß:** Mittlere tägliche Netto-Differenz 5m minus 15m in bp pro NY-Handelstag, **je Periode**; 95%-Intervalle rein deskriptiv.
- **Konservative Interpretation:** Ein positiver Unterschied alleine bedeutet **keine profitable Strategie**. Für vertiefte Forschung müssten absolute Nettoerträge in *beiden* Perioden auch unter Stress positiv sein; selbst dann unabhängiger neuer Test nötig.

## C. Technisches Audit, vor der echten Messung

- SHA256-Sperre auf R19-Runner `a626bce4bad126e372247bb15c061c861ebc2b8b5cf9157c7c2e4340a8d88769`. Dieser sperrt selbst den originalen R12-Loader mittels SHA256.
- Synthetische Testfälle: New-York-DST Sommer/Winter; erstes 5m-Signal kann vor 15m auftreten; frühester Entry auf nächstem Open; festgestellte Opening-Range darf nicht mit Zukunftsdaten verändert werden; Datumspaarung beider Varianten; R19-Ausführungskern selbsttestet unklare Kerzen, Stop vor Ziel, Gaps und Zeitlimit.
- Echte Messung erst nach unabhängigen Tests, bestehendem R19-Resultat-Audit und unter neuem, bei Existenz verweigertem Zielverzeichnis `~/QuantResearch/R20_BTC_ORB_5m_15m/Sep2024_Dec2025_v1`.
- Kein Parameter-Tuning, keine Stop-/TP-/Range-Breiten-Suche. 5m vs 15m ist der **einzige** primäre Vergleich. Keine R19/R18-Neuberechnung als neue Evidenz.

## D/E/F. Entscheidungslogik, Grenzen, Archiv

- **Vorteil 5m:** Nur wenn gepaarte Differenz im Mittel positiv ist und nicht stark zwischen den beiden Perioden wechselt, als explorativen Kandidaten vermerken. Niedrige, instabile oder stresskosten-negative Nettos sind nicht wirtschaftlich bestätigt. Keine automatische Strategie-Einführung, kein Paper-Bot-Start.
- **Vorteil 15m:** Bestätigt R19 nicht, solange Gesamt-Nettos negativ sind. Varianten können beide verlieren.
- **Archiv:** Rohdaten-Hashes, eingefrorener R19-Code-Hash, R20-Code-Hash, alle Einzelergebnisse und Tagespaare, Ergebnisbericht. Ergebnisstatus **explorativ, nicht bestätigt**. Dieses 2024/2025-Fenster wird nicht erneut zum Blindtest.

### Bibliografie

1. Holmberg, U., Lönnbark, C., Lundström, C. (2013). *Assessing the profitability of intraday opening range breakout strategies*. Finance Research Letters, 10, 27–33. DOI: 10.1016/j.frl.2012.09.001.
2. Tsai, Y.-C. et al. (2019). *Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets*. IEEE Access. DOI: 10.1109/ACCESS.2019.2899177.
