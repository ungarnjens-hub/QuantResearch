# R10-V2 – Phase-B-Abschluss, Korrektur und gesonderte explorative Einmalfreigabe

**Datum:** 15.11.2026  
**Vorregistrierung:** `R10_V2_PHASE_A_BTC_IMPULS_FORTSETZUNG_UMKEHR_2026-11-15.md` (Commit `92c4a88`).  
**Umfang:** BTC-USDT Binance USD-M Futures, 5m Last-Trade-Kerzen 01.09.2024–31.12.2025. Keine ETH-/SOL-Messungen, kein Backtest, keine Orders, kein Zugang zu laufenden Bots.

## 1. Festgestellter Indexfehler, vor der ersten Messung berichtigt

Die Phase-A-Zeile `std(r[j-293],...,r[j-6])` enthielt **287 statt 288** 5-Minuten-Renditen. Dieser nicht-inhaltliche Off-by-one-Fehler wird vor dem ersten Zugriff auf reale Outcome-Renditen berichtigt auf:

- `r[k] := ln(C[k+1]/C[k])` im Python-Array, bei Entscheidungsindex `j`:
- **288 Vor-Impuls-Renditen:** `r[j-294:j-6]` (288 Werte, letzter Close bei `j-6`).
- **Impuls:** `ln(C[j]/C[j-6])`, sechs volle 5-Minuten-Renditen.
- **Vorlaufender Trend:** `ln(C[j-6]/C[j-30])`, 24 frühere 5-Minuten-Renditen.
- **Label:** `sign(Impuls) * ln(C[j+6]/C[j]) * 10_000` Basispunkte.
- **Gemeinsame Sperre:** Entscheidungen `j+1` bis `j+6` werden nach Auswahl eines Events ausgelassen.

Die Uhrzeit der für `C[j]` abgeschlossenen Kerze ist `open_time[j]+5min`. `C[j]` ist **kein garantierter ausführbarer Einstiegspreis**.

## 2. Festlegung der Jahresgrenze

Jeweils **294 Kerzen ausschließlich aus dem beginnenden Abschnitt** werden zur Warm-up-Berechnung verwendet. Ereignisse müssen samt 30-Minuten-Label vollständig in diesem Abschnitt liegen; Ereignissperren werden an der Abschnittsgrenze zurückgesetzt. Dadurch wird keine Vorperiode für ein verstecktes Warm-up verwendet. Zwei klar benannte Explorationsabschnitte:

- 01.09.2024 00:00 bis 01.01.2025 00:00 UTC (exklusiv)
- 01.01.2025 00:00 bis 01.01.2026 00:00 UTC (exklusiv)

2025 ist trotz späterer Kalenderlage **kein neuer unabhängiger Blindtest**. Beide Jahrabschnitte sind durch die vorhandenen historischen Arbeiten als vorbelastet zu behandeln.

## 3. Kontraste und statistische Grenzen

Ein einziger vorregistrierter Hauptkontrast wird gemessen: `Mittelwert(Y | trendkonform) – Mittelwert(Y | trendgegenläufig)`. Alle Gruppenmittel und -mediane, Fortsetzungsquote, Zahl Events und Zahl der UTC-Kalendertage werden vollständig berichtet. Mit 7-Tage-Blockbootstrap, 5.000 Resamples und Seed `20261115` erzeugte Perzentilintervalle sind **nur explorative Unsicherheitsangaben**; kein p-Wert, keine statistische Signifikanz, keine Kausal- oder Profitabilitätsbehauptung. Jede Gruppe sollte mindestens 40 Ereignisse aus 20 UTC-Tagen umfassen, anderenfalls ist das Ergebnis als datenarm zu kennzeichnen. Die gepoolte Effektgröße über beide Jahresabschnitte wird **ohne gepooltes Konfidenzintervall** berichtet, um unterschiedliche Kalender-Resampling-Definitionen nicht zu vermischen.

**Offenes wesentliches Problem:** Die im bisherigen R9-Nachaudit unzureichend kalibrierte Inferenzmethode wird nicht für R10-V2 als validierter Nulltest ausgegeben. Außerdem sind die Gruppen möglicherweise wegen anderer Marktbedingungen nicht kausal vergleichbar. Diese Studie bestätigt damit selbst bei positivem Delta keine handelbare Strategie.

## 4. Technischer End-to-End-Gate

Vor der Marktberechnung muss derselbe versionierte Runner `R10_V2_BC_einmalige_btc_messung.py` zunächst alle integrierten Synthetiktests bestehen und den Rohdatencheck wiederholen (16 Monatsdateien, 140.256 Zeilen, Binance-USD-M-Metadaten, UTC, vollständig abgeschlossene Kerzen, OHLC-/Volumenprüfung, Datei-SHA-256-Manifest im Output). Kein vorhandener Ergebnisordner wird überschrieben. Ein fehlgeschlagener Test blockiert den Lauf.

Ausgabe nur unter `~/QuantResearch/R10_V2_Explorativ/Sep2024_Dec2025_v1/` (neuer Ordner), keine Modifikation der originalen Parquets, des produktiven TradingLab oder der Freqtrade-Paper-Bots.

## 5. Freigabe

**Phase B:** Grundlegender Daten-/Zeit-/Synthetik-Audit vorbereitet, echte Null-Inferenz bleibt **nicht kalibriert**.  
**Phase C:** **Gesondert und ausschließlich für eine einmalige DESKRIPTIVE/EXPLORATIVE BTC-Auswertung mit eingefrorenen Parametern freigegeben.** Kein konfirmatorischer Test, keine Strategierentabilitätsprüfung. Wenn der lokale Preflight fehlschlägt, wird Phase C **nicht** gestartet. Ergebnis darf nicht nachträglich zur Optimierung des schon untersuchten Zeitfensters dienen.

## 6. Interpretation danach

Falls die Fortsetzungs-/Gegenbewegungs-Differenz interessant ausfällt, muss ein **separater** Forschungsschritt eine tatsächlich ausführbare Long-/Short-/Exit-Regel mit realistischen Gebühren, Spread, Slippage, Funding und risikojustierten Vergleichsmodellen **vor dessen unabhängiger Prüfung** definieren. Gewinne aus dem aktuellen Close-to-Close-Proxy sind noch keine Nettorendite.
