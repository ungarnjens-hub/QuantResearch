# R9: Phase-B-Statistik-Nachaudit (2026-11-14)

## Nachgewiesener Datenstatus
Nutzerseitiger Lesecheck über **32 Dateien** bestanden: BTC und ETH je 140.256 lückenlose, abgeschlossene 5-Minuten-Kerzen von 2024-09-01 bis 2025-12-31 einschließlich, OHLC plausibel, `volume_base` vorhanden und nichtnegativ. Binance USD-M Futures `last_trade`; Spalte `volume` im älteren Adapter war falsch. Preis/Volumen sind `Decimal`-Objekte, nicht gewöhnliche float-Spalten; Konvertierung für die statistische Verarbeitung kontrollieren. Der kombinierte Runner wiederholt die strikten Checks und registriert SHA-256 aller 32 Quellen. Er erzeugt **keine** echten Renditen oder Momentum-Ergebnisse.

## Synthetischer Kalibrierungsversuch
Ein fest kodierter, reproduzierbarer Test prüft eine einseitige Testentscheidung für die Differenz der bedingten Folge-Logrenditen nach M1 vs. B1: tägliche Paare aus Renditesummen und Ereigniszahlen; gepaarter zirkulärer 7-Tage-Moving-Block-Bootstrap, synthetisch 500 Ziehungen pro Datensatz. Approx. p-Wert über um die beobachtete Differenz zentrierte Bootstrap-Verteilung. Holm-Korrektur für drei Markt-Hypothesen als gesonderter Familientest. **Das ist keine allgemeingültige Kalibrierung für echte Kryptomärkte.**

Lokale künstliche Messung am 14.11.2026, 200 unabhängige Monte-Carlo-Wiederholungen je Szenario, Seed 20261114:

| Synthetisches Szenario | Positive Entscheide bei nominal 5 % | Beobachtete Rate |
|---|---:|---:|
| Unabhängiges Nullszenario mit gemeinsamen, seriell korrelierten Tagesschocks | 14/200 | 7,0 % |
| Nullszenario mit Volumen-Gruppenhäufigkeiten und regimeabhängiger Varianz | 18/200 | **9,0 %** |
| Künstliche starke positive Alternative (+0,002 mittlere Logrendite pro M1-Ereignis) | 200/200 | 100 % |
| Familie aus drei synthetischen Nullmärkten mit Holm | 13/200 | 6,5 % |

**Interpretation:** Bei der vorläufigen einseitigen Bootstrap-p-Wert-Regel ist die beobachtete Fehlalarmrate in diesen Szenarien zu hoch, um die Signifikanzregel ohne weitere Begründung freizugeben. 200 Wiederholungen begrenzen die Präzision dieser Schätzung. Die 200/200 Erkennung der bewusst großen künstlichen Alternative sagt nichts über die Power für kleine reale Effekte aus. Die Perzentil-Konfidenzintervalle können separat rein deskriptiv berichtet werden, ohne eine fehlerkontrollierte Signifikanz zu behaupten.

## Offene Freigaben
- **Kein Phase-C-Start.** Der Vorschlag, 2025 als Blindtest zu behandeln, bleibt unzulässig, soweit historische Forschung diesen Zeitraum bereits tangiert hat. Beide Jahre können derzeit explorativ ausgewertet werden; 2024 und 2025 dabei getrennt berichten.
- Geprüfte reale Vorregistrierung: `|30-Minuten-Rendite| / (sqrt(6)*Standardabweichung vorheriger 288 5m-Renditen) >=2`; erhöhtes Impulsvolumen gegenüber Median der vorherigen 288 5m-Kerzen; Volumen-Schwelle 1,5; Label nächste 30 Minuten in Impulsrichtung, nicht garantiert handelbarer Close-to-Close-PnL. Bei Abweichungen entscheidet die archivierte Phase-A-Fassung, die hier nicht erneut als Originaldatei geöffnet werden konnte.
- Die Nullregel und der Mehrfachtest bedürfen einer neuen **Versionierung vor dem ersten echten R9-Renditescore**. Alternativ können in einem strikt explorativen Lauf alle tatsächlichen Effekte und Bootstrap-KIs ohne konfirmatorisches p-Urteil berichtet werden. Das wäre kein unabhängiger statistischer Nachweis.
- Die ökonomische Messung realisierbarer Renditen nach Gebühren, Spread, Slippage, Funding und konkreter Ausführung ist eine eigene spätere Forschungsfrage. Die primäre R9-Größe ist ein Gruppenmittelwertunterschied, kein erzielbarer Trade-PnL.

## Ausführung / Artefakte
`R9_phase_b_final_statistics_audit.py --run` prüft den lokalen Bestand, registriert die Quell-Hashes und kalibriert das Verfahren synthetisch. Gibt `FAIL` aus, falls die als heuristische Diagnose angesetzte Fehlalarmrate von 5 % in einem Nullszenario überschritten wird; dies ist ein **Warnsignal, kein exakter Test auf die wahre Fehlalarmrate**. Im lokalen Vorversuch wäre dies ein `FAIL`. Schreibt ausschließlich nach `~/QuantResearch/R9_PhaseB_FinalAudit/` und niemals in TradingLab, Profile oder Bots. Die Ergebnisausgabe wird nicht überschrieben.
