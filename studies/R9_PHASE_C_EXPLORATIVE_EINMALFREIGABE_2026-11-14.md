# R9: Einmalfreigabe für explorative Phase C, keine konfirmatorische Freigabe
**Datum:** 14.11.2026  
**Basis:** R9 Phase A (`7bfbd53`), Datenfensternachtrag (`8348095`), Statistiknachaudit (`ed4bd41`), bestätigte lokale Datengates BTC+ETH mit je 140.256 Kerzen.  
**Nutzerentscheidung:** Zustimmung zum unmittelbar zuvor vorgeschlagenen ausschließlich explorativen Lauf.

## Zweck
Eine einmalige deskriptive R9-Messung an historischen BTC/ETH Binance USD-M Perpetual 5m-Kerzen 2024-09-01 bis 2025-12-31, strikt getrennt nach September–Dezember 2024, Januar–Dezember 2025 sowie gemeinsamem Gesamteffekt. Beide Jahresabschnitte sind **explorativ**; keine Behauptung eines unberührten Holdouts. SOL ist mangels lokaler 2024/25-Daten nicht Teil der Messung; ursprüngliche drei-Markttestfamilie bleibt dokumentiert und wird nicht günstig uminterpretiert.

## Unveränderliche Definitionen
- Preisimpuls über sechs abgeschlossene 5m-Renditen, z-Score mittels Stichproben-SD von 288 **vor Impulsbeginn** bekannten Renditen, Schwelle `z>=2.0`, Richtung `sign(impulse)`.
- Handelsvolumen aus `volume_base` der sechs Impulskerzen geteilt durch sechsmal Median der 288 **vor dem Impuls** bekannten 5m-Volumenkerzen.
- `M1: v>=1.5`, `B1: v<1.5`. Nach einem ausgewählten Ereignis beide Gruppen für die folgenden sechs 5m-Entscheidungszeitpunkte sperren.
- Auswertungsziel `Y=sign(impulse) * log(C(t+30m)/C(t))`; primär `Delta=mean(Y|M1)-mean(Y|B1)`, in Basispunkten (`*10000`).
- Keine 2024-Labels über den 2024/25-Jahreswechsel. Im Jahr 2025 dürfen ausschließlich bereits abgeschlossene 2024-Kerzen als Warm-up genutzt werden. UTC-Kerzenschluss = `open_time +5min`.
- Paariger zirkulärer Moving-Block-Bootstrap auf 7 vollständigen UTC-Kalendertagen, 5000 Ziehungen, Seed 20261114. 95%- und Bonferroni-98,333%-Intervalle **nur deskriptiv**.
- Registrierte Mindestgates pro Markt und Gruppe: 40 Ereignisse und 20 unterschiedliche UTC-Tage, mindestens 99% gültige Bootstrap-Replikate. Vorregistrierte Forschungsschwelle +10bp ist **kein** handelsökonomischer Breakeven-Wert.

## Zwingende Begrenzung
Die frühere synthetische Kalibrierung zeigte bis zu 9% Fehlalarme. Deshalb werden Bootstrap-Intervalle nicht als gültiger Signifikanztest interpretiert, selbst wenn sie Null ausschließen. Kein p-Wert, kein Holm-Nachweis, keine Kausalität. Die rohe Differenz zwischen M1 und B1 kann an Volatilität, Impulsstärke, Marktregimen und Tageszeiten liegen.

Die verwendeten Signal-Schlusskurse sind **nicht** zu garantierten Orderpreisen ausführbar. Gebühren, Spread, Slippage, Funding und Liquiditätswirkung fehlen. Eine positive Differenz oder positive `Y` zeigt **keine** Strategieprofitabilität.

## Reproduzierbarkeit und Isolation
Runner `R9_explorative_momentum_2024_2025_v1.py`, SHA-256 `1b8a0316ee4673d940c908b4a1041879d24fd0e39bc4ad2c4cb74e60378034e5` (vor lokaler Git-Archivierung prüfen). Vor der Messung Synthetik-Preflight und SHA-/OHLCV-/UTC-/Herkunftsgates; Quellen bleiben nur lesend. Ausgaben nur im neuen, gegen Überschreiben geschützten Ordner `~/QuantResearch/R9_Explorativ/Sep2024_Dec2025_v1/`: Ergebnis-JSON und vollständiger Markdown-Bericht. Keine Strategie, keine Paper-Bots oder Freqtrade-Schnittstelle berühren.

**Freigabestatus:** EINMALIGE EXPLORATIVE REALDATENMESSUNG FREIGEGEBEN. KONFIRMATORISCHE PHASE C / PHASE E / PNL NICHT FREIGEGEBEN.
