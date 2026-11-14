# R8-A: Technisches Methodenaudit der Korrelation (Phase B)

**Datum:** 14.11.2026  
**Status:** **PASS** für den geprüften *synthetischen technischen Korrelationsteil*; **NO-GO** für Messung an echten Marktdaten.  
**Grundlage:** `R8_PHASE_A_NACHTRAG_V02_2026-11-14.md` und `R8_METHODENAUDIT_PHASE_B_2026-11-14.md`. Kein Ergebnis aus R5/R6/R7 wurde neu ausgewertet.

## Auftrag und Datenabgrenzung

Geprüft werden exakt drei vordefinierte Paare: BTC–ETH, BTC–SOL, ETH–SOL. Verwendet wurden ausschließlich generierte synthetische 5-Minuten-Schlusskurse und daraus gebildete Logrenditen. **Alle unten genannten Korrelationen sind künstliche Kontrollwerte, keine Binance-Marktstatistiken.** Weder Marktdaten noch produktive TradingLab-Dateien wurden gelesen.

## Implementierte Methodik

- 92 komplette UTC-Kalendertage × 288 Renditen/Tag = **26.496** vollständig synchronisierte 5-Minuten-Renditen; aus den Schlusskursen wurden Renditen mit expliziter *Open-Time→Close-Time*-Konvention abgeleitet.
- Pearson-Korrelation der Renditen, nicht der Kursniveaus, auf **identischer gemeinsamer Stichprobe** für alle Paare.
- Vorzeichenübereinstimmung pro Paar nur wenn beide Renditen **ungleich null** sind; vollständige Nenner und ausgeschlossene Fälle erfasst.
- Gepaartes Moving-Block-Resampling in **7 zusammenhängenden Kalendertagen**, 5.000 Resamples, ein einziger Indexsatz für alle drei Paare, Seed `20261114`; 95%-Perzentilintervalle.
- Korrelation wird pro Resample auf Basis der **gepoolten Zeilen** ermittelt, nicht als ungewichteter Durchschnitt von Tageskorrelationen. So bleiben identische Zeitpunkte und Stichprobenumfänge erhalten.
- **Randtagsregel der technischen Implementierung:** Unvollständige erste/letzte UTC-Tage werden abgewiesen. Für eine Marktuntersuchung muss der Vor-Schlusskurs für die erste 5-Minuten-Rendite bereits vor dem Fenster zuverlässig verfügbar sein. Kein stilles Abschneiden, Füllen oder Verschieben des Zeitraums.

## Synthetische Kontrollzahlen – ausdrücklich keine Marktresultate

| Paar | künstlicher Pearson-r | künstliches 95%-Intervall | künstliche Vorzeichenübereinstimmung | nichtnullige Paare | nullausgeschlossene Zeilen |
|---|---:|---|---:|---:|---:|
| BTC–ETH | 0.6579 | [0.6522, 0.6632] | 72.87 % | 26,069 | 427 |
| BTC–SOL | 0.6650 | [0.6603, 0.6704] | 73.32 % | 26,109 | 387 |
| ETH–SOL | 0.6695 | [0.6615, 0.6796] | 73.70 % | 26,150 | 346 |

Die positiven künstlichen Werte wurden gezielt durch einen geteilten simulierten Faktor erzeugt. Sie können *keine* Aussage über tatsächliche BTC-/ETH-/SOL-Korrelationen liefern.

## Kontroll- und Fehlertests

**18/18 im finalen Lauf bestanden:** all_three_pairs, time_open_close, closed_returns_no_lookahead, 92_complete_days, pairwise_zero_policy, pearson_numpy_crosscheck, unit_scale_invariance, paired_block_resampling, deterministic_seed, partial_day_rejected, missing_candle_rejected, duplicate_rejected, nan_rejected, nonpositive_price_rejected, misaligned_open_rejected, independent_returns_control, perfect_negative_control, zero_variance_rejected.

Unabhängiger NumPy-`corrcoef`-Abgleich, Skaleninvarianz, Paarzählung der Nullrenditen sowie zusätzliche unabhängige, perfekt negativ korrelierte und degenerierte Konstantreihen wurden geprüft. Fehlende 5-Minuten-Zeile, duplizierter Zeitpunkt, Teil-UTC-Tag, NaN, nichtpositiver Schlusskurs und zeitverschobene Open-Timestamps führten zu *FAIL-CLOSED*.

**Auditnotiz zum Testablauf:** Ein anfänglicher zusätzlicher Test verlangte fälschlich, dass bei jeder Stichprobe unabhängiger Zufallsreihen jedes 95%-Bootstrap-Intervall die Null enthalten müsse. Das ist keine gültige deterministische Anforderung: Bei einer Stichprobe darf die Null trotz unabhängigem Erzeugungsprozess außerhalb des Konfidenzintervalls liegen. Die unzulässige Assertion wurde entfernt und durch eine testbare technische Invariante (Intervall enthält den beobachteten Punktschätzer bei diesem Kontrollfall) ersetzt. Die finale Prüfversion ist archiviert; keine Marktdatenmessung wurde dadurch beeinflusst.

## Grenzen, ausstehende Freigabegates

1. Die synthetische Kontrolle validiert Berechnung und Datenhygiene, **nicht** Bootstrap-Deckungswahrscheinlichkeit bei realistischen Abhängigkeitsstrukturen. Insbesondere können Regimewechsel die 7-Tage-Blocklänge problematisch machen; keine behauptete Kalibrierungsfreigabe.
2. Die fachliche Auswahl des explorativen R8-A-Zeitraums August–Oktober 2026 und des Datenquellen-/Verbrauchsregisters muss noch abschließend bestätigt werden. Dieser Zeitraum ist aus R5/R6 **verbraucht** und darf ausschließlich deskriptiv verwendet werden.
3. Bei echten Rohdaten sind Vollständigkeit, Preissemantik, Zeitzone, Informationsverfügbarkeit und ursprüngliche Quellenchecks separat nachzuweisen. Kein impliziter `inner join`, der Datenlücken kaschiert.
4. **R8-B** (gerichtete BTC→SOL-Logit-Prognose) wurde hier ausdrücklich **nicht** statistisch kalibriert; ihr Phase-B-Gate bleibt offen.
5. Kein Kausalitätsnachweis, keine Vorlauf- oder Handelbarkeitsaussage.

## Reproduzierbarkeit

- Skript: `R8_phase_b_korrelations_audit.py`; SHA256 `bfcca6d2373b162089c27819f302eac3a3dd182c310c90683752cdc6af78f63d`.
- JSON: `R8_phase_b_korrelations_resultat.json`; SHA256 `f81287cc47dbba361e9ad214f58a151dfe9f2e05a540409e2a5658448e2d4b76`.
- Umgebung: Python `3.13.5`, NumPy `2.3.5`, pandas `2.2.3`.
- Befehl: `python R8_phase_b_korrelations_audit.py` (erzeugt JSON nur neben dem Skript; keine Netzwerkanfragen).

**Entscheidung:** R8-A-Berechnung im technischen synthetischen Umfang **PASS**. Forschung R8 insgesamt weiterhin **Phase B / NO-GO** für echte Marktdaten. Nächster sinnvoller Schritt: Datenregister und festes Qualitätsgate abschließen, separat R8-B-Nullkalibrierung durchführen.
