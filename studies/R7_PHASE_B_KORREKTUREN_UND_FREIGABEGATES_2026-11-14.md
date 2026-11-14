# R7 – Phase-B-Korrekturen und Freigabegates

Stand: 2026-11-14. Status: **NO-GO für Ergebnismessung**. Grundlage: `R7_FORSCHUNGSDESIGN_PRAEZISIERT_2026-11-14.md` (Commit d635836) und `R7_FACHAUDIT_B2_M2_2026-11-14.md`.

## 1. Fachliche Entscheidung

- **Primärfrage:** Hat BTC-HAR einen zusätzlichen *bedingten* OOS-Prognosenutzen für ETH-log-RV über ETH-HAR und SOL-HAR hinaus?
- **B2:** Intercept + ETH-HAR(12, 288, 2016) + SOL-HAR(12, 288, 2016).
- **M2:** B2 + BTC-HAR(12, 288, 2016).
- **Ein einziger primärer Zielmarkt:** ETH. SOL dient ausschließlich als zusätzlicher Informationsproxy. Keine Behauptung kausaler BTC-Übertragung, keiner vollständigen Kontrolle gemeinsamer Marktschocks. Keine zusätzlichen Modellvarianten.
- Modelle sind *verschachtelt*. Clark–West (2007) zeigt eine besondere Nullverteilung/Schätzrauschproblematik für ungeprüfte Gleichheits-Tests von MSPE. Ein naiver HAC-p-Wert auf Roh-Verlustdifferenzen ist **nicht allein** als formal kalibrierter Test der verschachtelten Modellnull zu interpretieren.

## 2. Primäre Effektgröße und robuste Berichtslogik

Primär zu berichten: `100 × (MSE_B2 − MSE_M2) / MSE_B2`, gepaarte Fehler auf identischen Prognosezeitpunkten.

**Vorläufiges Gate, noch nicht final freigegeben:** 95%-Intervall des relativen MSE-Gewinns mit gepaartem Moving-Block-Bootstrap auf Kalendertagen (7-Tage-Blöcke; 5.000 Ziehungen; Seed 20261114). Intervall misst Unsicherheit *unter den Annahmen des verwendeten Resamplings*. Ein 90-Tage-Test mit 7-Tage-Blöcken ist begrenzt belastbar. Mehrere Modellrefits, Nichtstationarität und verschachtelte Modelle können die nominelle Abdeckung beeinträchtigen. Die effektive Abdeckung ist vor Marktmessung durch synthetische Simulation unter passender Null und mindestens einer Alternative zu überprüfen. **Bei unzureichender Kalibrierung keine Messfreigabe**, stattdessen methodische Revision vor Datenkontakt.

**Sekundärdiagnostik (nicht entscheidungsersetzend):** Tages-HAC auf ungeadjustierten Verlustdifferenzen; dazu als fachlich begründeter Vergleich Clark–West-adjustierte Verlustdifferenz `d_CW,t = e_B2,t² − e_M2,t² + (f_B2,t − f_M2,t)²`. Bei expandierendem monatlichem Refit und abhängigen Zielwerten ist eine asymptotische Standardnormal-Kalibrierung *nicht ohne methodischen Nachweis garantiert*. Clark–West darf **nicht nachträglich zum günstigeren Entscheidungstest** erhoben werden.

## 3. Ex-ante-Entscheidungstabelle (bis zur Kalibrierung vorläufig)

| MSE-Punktschätzer | 95%-Intervall | Interpretation |
|---|---|---|
| > 0 | vollständig > 0 | Evidenz für positiven OOS-Zusatznutzen **unter den kalibrierten Testannahmen** |
| beliebig | umfasst 0 | **Ungeklärt**: keine hinreichend präzise Evidenz |
| < 0 | vollständig < 0 | Evidenz für schlechtere OOS-Prognoseleistung des größeren Modells im geprüften Zeitraum |

Ein kleiner/negativer Punktschätzer **allein** ist keine statistische Widerlegung. Ob ein formaler p-Wert als ergänzendes Gate verlangt wird, ist in der finalen, vorab versionierten Protokollfassung **vor jeder Marktmessung** festzulegen und mit einem geeigneten Null-Kalibrierungstest zu begründen. Keine nachträgliche Auswahl der Teststatistik.

## 4. Zeit, Daten und technische Gates

- 5m-Kerzen sind über ihre **Open-Time** indiziert. `hh:55` ist erst **nach** Kerzenschluss `hh+1:00 UTC` informationell verwendbar. Forecasting ab diesem Zeitpunkt, nicht bei Kerzenöffnung.
- Label ist erst nach Ende des vollständigen 60m-Zielfensters verfügbar (`forecast_index + 65m`); nur solche Trainingszeilen vor jedem Monats-Refit.
- Prospektives Testfenster **vorgeschlagen**: 2027-01-01 00:00 UTC bis 2027-04-01 00:00 UTC exklusiv. Zeitraum vor seiner vollständigen Verfügbarkeit weder teilweise auswerten noch nachträglich verschieben.
- Gemeinsame historische Trainingsabdeckung von BTC, ETH und SOL muss **vor Messung** mit unverändertem Startregelwerk und 2016-Bar-Warm-up überprüft werden. Training 2024-09-01 ist eine Designabsicht, **keine bereits geprüfte Datengate-Zusage**.
- Einheitliche Quelle/Preissemantik/UTC, keine Duplikate und Lücken, eindeutige Verfügbarkeitszeitpunkte. Rohdaten, laufende Bots und produktive Dateien nicht ändern.
- Synthetisches Gate: Index/Verfügbarkeitszeit, kein Ziel-Leakage, kein Rollover-Leakage, Trainingsendgrenzen, Refit-Monatswechsel, 3-Markt-Merge, korrekte OLS-Rangbehandlung und Fehlerzustände, Tagesaggregation, reproduzierbares Bootstrap und unzulässige Daten abweisen.
- **Datenregister:** R1–R6 und alle anderen untersuchten Zeiträume registrieren. R5/R6-Validierungsperiode Aug–Okt 2026 ist verbraucht. Testfenster 2027 auf Vorverwendung prüfen, bevor irgendwelche Ergebnisse bekannt werden.

## 5. Vorabregistrierte Entscheidungsreihenfolge

1. Dieses Audit samt noch offenen Gate-Punkten dokumentieren und versionieren.
2. Literaturbasierte Entscheidung über die **finale** Inferenzmethode unter verschachtelten Modellen und zeitlicher Abhängigkeit; geeignete synthetische Kalibrierung fixieren.
3. Präzise Spezifikation der OLS-Fehlerbehandlung (Rang-/Konditionsschwelle, keine stillen Datenverluste), der Zeitachsen und der Testfallmatrix.
4. Getrennte technische Phase-B-Prüfung auf rein synthetischen Daten **ohne Auswertung historischer oder künftiger ETH/SOL-Prognosefehler**.
5. Erst nach bestandenem Methodik-/Daten-/Integritätsgate **explizite Phase-C-Freigabe**.

## 6. Literatur

- Clark, T. E. & West, K. D. (2007): *Approximately normal tests for equal predictive accuracy in nested models*. J. Econometrics 138, 291–311. doi:10.1016/j.jeconom.2006.05.023.
- Giacomini, R. & White, H. (2006): *Tests of conditional predictive ability*. Econometrica 74, 1545–1578. doi:10.1111/j.1468-0262.2006.00718.x. Deren Rahmen mit endlichen rollierenden Schätzfenstern ist **keine direkte Garantie** für das vorliegende expandierende Refit.
- Künsch, H. R. (1989): *The jackknife and the bootstrap for general stationary observations*. Ann. Statist. 17, 1217–1241. doi:10.1214/aos/1176347265.

**Wichtig:** Dieses Papier verschärft die Methodik, ersetzt nicht stillschweigend die zuvor versionierte R7-Spezifikation. Noch keine Marktmessung und keine Methodenfreigabe.
