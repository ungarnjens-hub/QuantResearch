# R5/R6: Unabhängiges Codeaudit der zeitlichen Validierung

**Prüfdatum:** 14. November 2026  
**Gegenstand:** hochgeladenes Archiv `R5_R6_Validierung_AugOkt2026.zip`  
**Archiv-SHA256:** `9ecf1fe9c7da899582e23c7f1a409f03c13ad0fb239a2b46a8ee7f143c9a8bb7`  
**Urteil:** Statisches Implementierungs- und Integritätsaudit überwiegend bestanden; numerische unabhängige Reproduktion **noch offen**. Positive Validierungsbefunde vorläufig.

## 1. Nachgewiesene Integrität

Die enthaltenen Artefakte stimmen mit den im Ergebnis-JSON eingebetteten Hashes überein:

| Artefakt | SHA256 |
|---|---|
| `frozen_code/R5_R6_Validierungsrunner.py` | `4d54470a0a4dd9c825311698436da09888a6aaaebbfebd94b2147ff05b9dddbf` |
| `frozen_code/R5_R6_Validierungsprotokoll_PhaseB_2026-11-14.md` | `ba46b172bb9cf4e51dea4241804423a052c69abcd42cd6fc1b033bbea2fd5df8` |
| `frozen_code/R5_R6_Methodenaudit_2026-11-14.md` | `000c4c30d40a28bedaf9795be11c25c51daf12e6a97f83a75ee10a3ceaf4f04e` |
| `data/manifest.json` | `1bd96c1ae1b453118b65f157c5f7a50e1fd623dbca33b4a48b96655bda6008e1` |

Die Freigabe nennt den Code-Commit `655ca01f1fca83594a827a5db8765c1136fa78f5`. Die tatsächliche Repository-Historie wurde außerhalb des Archivs nicht eigenständig verifiziert. Die Manifestangaben zu den drei Kursdateien sind vorhanden; die Parquet-Dateien selbst sind nicht Bestandteil dieses Audits.

## 2. Statische Codeprüfung

- **Keine ersichtliche Zukunftsinformation:** `features()` bildet vergangene Renditen über rollende Fenster; die künftige Zielgröße wird getrennt über `.shift(-12)` konstruiert. `available` entspricht `t+65min` für den Zeitstempel der eröffneten 5m-Kerze. Ein Forecast zur Minute 55 verwendet Merkmale, die erst mit Kerzenschluss `t+5min` vollständig bekannt sind. (`Runner: 145–156`)
- **Training vor dem Monatswechsel:** `forecast()` filtert Training auf `data.index >= 2024-09-01` und `data.available <= month`; die Refit-Termine sind August, September und Oktober 2026, expandierendes Training. Die Spalten von B0, B1 und M1 entsprechen dem Protokoll. (`159–177`)
- **Vollständigkeit:** Die 2.207 Zeitpunkte und Tagesverteilung (91 Tage mit 24, letzter Tag 23 Prognosen) werden explizit geprüft. (`180–190`)
- **Statistik:** täglicher Mittelwert von `d = e_B1²-e_M1²`, Intercept-HAC Bartlett mit sieben Tageslags, einseitige Normalapproximation; sieben Tage lange, gepaarte Moving-Blocks, 5.000 Resamples und Seed 20261114; Holm für zwei Märkte ist im Code umgesetzt. (`193–254`, `334–341`)
- **Mess-Gate:** prüft frozen-file-Hashes, Freigabeflag, Manifest-Metadaten, Datenhashes und verhindert einen zweiten Lauf, sofern das Ergebnisverzeichnis vorhanden ist. (`305–350`)

## 3. Relevante Einschränkungen

1. **Keine zeilenweise Nachrechnung:** Die zwei Forecastdateien `results/ETH_forecasts.csv` und `results/SOL_forecasts.csv`, die der Runner erzeugt, fehlen im gelieferten Archiv. Eine unabhängige numerische Berechnung der MSEs, Bootstrap-Grenzen und HAC-p-Werte ist somit **noch nicht durchgeführt**. Das ist derzeit der wichtigste offene Punkt.
2. **Quellrohdaten nicht beigefügt:** Manifest-Hashes allein erlauben keinen unabhängigen Abgleich mit den tatsächlichen Parquet-Dateien. Für die Statistikkontrolle reichen zunächst die Forecast-CSV-Dateien; für eine vollständig eigenständige Prognosereproduktion werden zusätzlich die eingefrorenen Eingabedaten benötigt.
3. **Explorative Vorgeschichte:** Frühere Forschung und Marktexposition bedeuten, dass die Unverbrauchtheit der August–Oktober-Periode nicht mathematisch nachweisbar ist; im Protokoll selbst wird dies korrekt eingeschränkt.
4. **Kleine effektiv unabhängige Stichprobe:** 92 Tagesaggregate und nur rund 13 Wochen. Die Normalapproximation und der 7-Tage-Blockbootstrap sind festgelegt, aber ihre Konfidenzintervalle und p-Werte bleiben approximativ.
5. **Geringfügige Gewichtungsdifferenz:** Das globale MSE gewichtet jeden Forecast gleich (letzter Tag 23 statt 24 Forecasts), der tägliche HAC-Test gewichtet jeden Tag gleich. Das ist nachvollziehbar, aber formal nicht exakt dieselbe gewichtete mittlere Verlustdifferenz wie im globalen MSE-Ziel. Ein kleiner, vorab bestehender Methodikversatz; keine rückwirkende Korrektur auf dem verbrauchten Testset.
6. **Statisches Audit ist keine Ausführung:** Die synthetischen Selbsttests wurden auf dem Nutzersystem laut Konsolenausgabe bestanden; hier wurde der Runner nicht gegen lokale Rohdaten ausgeführt. Die Featureidentität gegenüber R5/R6 ist durch die externen, gehashten Code-Dateien im Runner vorgesehen, aber im gelieferten Archiv fehlen die Originaldateien selbst.
7. **Keine Handelsaussage:** Statistische Verbesserung der Prognosegenauigkeit beweist keine Kausalität und keinen Vorteil nach Kosten, Liquidität, Slippage oder Funding.

## 4. Dokumentierte Ergebnisse (noch nicht unabhängig neu berechnet)

| Markt | N | Relative MSE-Verbesserung | 95%-Bootstrap-Intervall | Holm-p | Status |
|---|---:|---:|---|---:|---|
| ETH | 2.207 | +1,62476 % | [+0,71249 %, +2,50837 %] | 0,00038045 | Vorläufig positiv |
| SOL | 2.207 | +2,11242 % | [+0,54369 %, +3,65057 %] | 0,00378612 | Vorläufig positiv |

## 5. Entscheidung und nächster Schritt

**Codeaudit statisch: bestanden mit Einschränkungen. Numerische Reproduktionsfreigabe: offen.** Keine Modelländerung, kein erneuter Markttest, keine nachträgliche Optimierung. Im nächsten Schritt ausschließlich die bereits erzeugten beiden CSV-Dateien mit Prognosen sichern und daraus alle aggregierten Kennzahlen *unabhängig* neu berechnen. Falls Abweichungen entstehen, diese dokumentieren; niemals den verbrauchten Holdout durch neue Parameter- oder Fensterwahl reparieren.
