# R9 – Versionierter Phase-B-Nachtrag: historische Datenfenster 2024/2025

**Datum:** 14.11.2026 · **Bezug:** R9 Phase A `7bfbd53`, Phase B `5c14cd3`, Technik-Audit `e7969c3`
**Status:** Forschungsdesignkorrektur *vor* R9-Marktmessung. Phase C weiterhin gesperrt.

## Grund für die Änderung
Die ursprüngliche Population enthielt BTC, ETH, SOL im bereits verwendeten August–Oktober-2026-Fenster. Der Nutzer hat **vor R9-Ergebniseinsicht** 2024/2025 gewünscht. Das Dateiinventar weist Binance-USD-M-Perpetual-Last-Trade-5m-Daten für BTC und ETH vollständig von 2024-09-01 00:00 UTC bis 2026-01-01 00:00 UTC (exklusiv) aus. Der August 2024 ist nur teilweise vorhanden und wird ausgeschlossen. Lokale SOL-5m-Quelldateien für 2024/2025 fehlen. Diese Änderung ist nicht durch beobachtete Momentum-Ergebnisse motiviert.

## Verbindliche Datenfenster
- **Märkte:** BTC/USDT:USDT und ETH/USDT:USDT, **getrennte** Auswertung. SOL = `NO DATA`, ohne Ersatzergebnis.
- **2024:** 2024-09-01 00:00 UTC bis 2025-01-01 00:00 UTC (exklusiv), **explorative Teilperiode**.
- **2025:** 2025-01-01 00:00 UTC bis 2026-01-01 00:00 UTC (exklusiv), **zeitlich nachgelagerte, ebenfalls explorative Teilperiode**. Keine Behauptung eines unverbrauchten Blindtests, weil andere Studien Daten aus 2025 bereits verwendet haben und kein abschließendes Nutzungsregister vorliegt.
- **Primärer historischer Vergleich:** getrennt für BTC und ETH über September 2024 bis Dezember 2025, sofern alle Daten- und Event-Gates bestehen. Beide Jahresabschnitte werden zusätzlich getrennt berichtet, ohne nachträgliche Auswahl des besseren Jahres.
- **Sperr- und Grenzregel:** 2024-Zukunftslabels dürfen den UTC-Jahreswechsel nicht überschreiten. Für 2025 ist ausschließlich Vergangenheit vor dem Signal (einschließlich 2024-Warm-up) erlaubt, jedoch keine übergreifende 2024-Labelauswertung. Beim ersten verfügbaren Signal muss die vollständige 288-Renditen-Vorgeschichte existieren. Ereignissperre pro Markt gilt kontinuierlich über den gesamten zusammenhängenden Datenbestand.
- **Kein 2027-Blindtest fest reserviert:** Die früher vorgeschlagene Juli–September-2027-Reservierung wird für R9 bis zu einer gesonderten ausdrücklichen Nutzerentscheidung als **nicht beschlossen** geführt. Die anderweitig reservierten Perioden für R7 und R8 werden nicht angetastet.

## Unveränderte Methodik
Die in R9 Phase A registrierten Bedingungen werden **nicht** anhand von Marktergebnissen verändert: 30m-Impuls (6 x 5m), 288 vorherige 5m-Renditen für `sigma5` (Stichproben-SD), `z >= 2.0`, Volumenverhältnis `v >= 1.5` vs. `<1.5`, sechs 5m-Schlusszeitpunkte gemeinsame Ereignissperre, 30m-signierte Close-to-Close-Logrendite als **nicht ausführbarer** Mechanismusproxy. 7-Tage-Kalendertags-Blockbootstrap, 5.000 Ziehungen, Seed `20261114`; Primärdelta = `mean(M1)-mean(B1)`.

Die im Phase-B-Nachtrag festgelegten Mindestgates bleiben: je Gruppe/Markt mindestens 40 Ereignisse auf mindestens 20 Tagen; >1% ungültige Bootstrap-Ziehungen = `UNGEKLÄRT`; Mindest-Punktschätzer +10 bp sowie positiver M1-Rohmittelwert. Die ursprüngliche Bonferroni-Testfamilie von **drei** Märkten wird **konservativ beibehalten** (98,333…%-Perzentilintervalle), selbst wenn wegen der SOL-Datenlücke nur zwei Märkte messbar sind; keine nachträgliche Lockerung. Diese Bootstrap-Screens sind vorerst explorativ, ohne bestätigte Nulltest-Kalibrierung und ohne p-Wert-/Handelsertragsbehauptung.

## Vor Messung verpflichtend
1. Die 34 Monatsdateien **nur lesend** prüfen: Herkunftsmetadaten soweit lokal nachweisbar, UTC-Raster, exakte Monatsgrenzen, lückenlose Synchronisierung, positive valide OHLCV, Duplikate, SHA-256 jedes Originals; die frühere Dateinamenprüfung ist **kein** vollständiger Provenienznachweis. Wenn Binance-Endpunkt/Herkunft nicht unabhängig belegbar ist, `PROVENIENZ_UNVERIFIZIERT`, kein bestätigter Datengate-PASS.
2. Das absolute Konsolenprotokoll der Datengates sowie einen lokalen Hash-Manifest-Snapshot isoliert unter `~/QuantResearch/R9_2024_2025_Audit/` ablegen, **nicht** in TradingLab. Keine Rohdaten in Git.
3. Vor einer Markt-Renditemessung Runner technisch und synthetisch prüfen (Off-by-one, Historie, Jahreswechsel, Sperrregel, Bootstrap, kein Look-ahead, z-/v-Grenzen). Verteilung der Ereignisse oder Zielrenditen **nicht** vor der ausdrücklichen Phase-C-Freigabe ansehen.
4. Für eine inferenzielle Bestätigung bleiben reale Nullkalibrierung, unabhängiger neu registrierter Holdout und ökonomischer Ausführungstest ausstehend.

**Entscheidung:** Nur Phase-B-Daten- und Methodenaudit freigegeben. `R9 PHASE C: NOT APPROVED`. Keine Handelsstrategie, kein Paper-/Live-Handel, kein Freqtrade-Backtest.
