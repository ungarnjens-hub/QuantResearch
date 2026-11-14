# R8 – Abschlussaudit des synthetischen 600er-Kalibrierungslaufs

**Status: Phase-B-Kalibrierung abgeschlossen und Einzelresultate konsistent. Keine Phase-C-Freigabe.**

Datenquelle: ausschließlich simulierte 5-Minuten-Kurse. Berichtsstand: 14.11.2026.
Auditart: erneute Aggregation der gespeicherten 600 Einzelresultate; **keine erneute Simulation**.

| Szenario | Positive Gates | Anteil | Exaktes binomiales 95%-KI | Mittlere absolute Log-Loss-Differenz |
|---|---:|---:|---|---:|
| `independent_null` | 2/200 | 1.00 % | [0.121 %, 3.565 %] | -0.0000080779 |
| `common_factor_null` | 1/200 | 0.50 % | [0.013 %, 2.754 %] | -0.0000080272 |
| `lagged_btc_alternative` | 200/200 | 100.00 % | [98.172 %, 100.000 %] | 0.0119090173 |

## Prüfumfang

- Drei Dateien mit je 200 Simulationsresultaten, durchgehende feste Seeds, keine Doppelungen.
- Signifikanz-Gate jeder Replikation nachgerechnet: `delta > 0` und `CI_low > 0`.
- Log-Loss-Differenzen, Prognosezahlen, Null-Labels und Zusammenfassung gegengeprüft.
- Freigabedatei, Code-, Runner- und Protokoll-SHA-256 geprüft; keine FAILURE.json.
- Einzelresultate, summary.json und vorhandenes Laufprotokoll unter SHA-256 im Manifest registriert.
- Roh-Evidenz verbleibt lokal im bestehenden Laufordner und im separaten ZIP unter `~/Downloads/Marktforschung`. GitHub erhält nur Bericht und Manifest; kein Marktpreisdatensatz.

## Grenzen und Freigabeentscheidung

Die beiden Nullszenarien zeigten wenige positive Gates. Das spricht für niedrige Fehlalarmhäufigkeit **unter diesen synthetischen Annahmen**. Es garantiert keine globale Kontrolle unter unbekannten Marktprozessen. In der fest eingebauten Alternative wurden alle positiven Gates erkannt. **Schwache tatsächliche Vorlaufeffekte, Modellmissspezifikation und zeitliche Marktveränderungen sind hierdurch nicht hinreichend geprüft.**

**Phase B (synthetische Kalibrierung): abgeschlossen, mit Einschränkungen.**
**R8-A echte explorative Korrelation:** gesonderte Datenregister-/Methodenfreigabe erforderlich.
**R8-B Blindtest:** **NO-GO**, prospektives Testfenster und volle methodische Freigabe bleiben geschützt.
**Keine Tradingstrategie, keine Kausalbehauptung, keine Profitabilitätsaussage.**
