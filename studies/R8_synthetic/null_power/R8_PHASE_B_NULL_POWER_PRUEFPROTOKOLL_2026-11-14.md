# R8-B: statistisches Null-/Power-Prüfprotokoll, Phase B
Datum: 2026-11-14. Status: ENTWURF, **keine Freigabe zur Hauptkalibrierung oder Marktmessung**.

## Prüfziel
Kontrollieren, wie oft die **festgelegte** R8-B-Regel (positive gepaarte OOS-Log-Loss-Differenz und positive untere 95%-Grenze des 7-Tages-Moving-Block-Bootstraps) unter einer *bedingten* Nullhypothese fälschlich einen Zusatznutzen von BTC meldet. Dazu Power unter einer künstlich gesetzten alternativen DGP bestimmen. Korrelation ist dabei vom gerichteten Informationsbeitrag zu unterscheiden.

## Unveränderlicher Prognosevertrag
Genau die Funktionen `build`, `training_rows`, `fit_predict`, `score`, `bootstrap` und die Zeitschranken `TRAIN_START=2025-01-01`, `TRAIN_END=2027-01-01`, `TEST_START=2027-04-01`, `TEST_END=2027-07-01` aus `R8_phase_b_synthetischer_e2e_test.py` verwenden. Keine gesperrten Daten 2027-01-01 bis 2027-04-01 erzeugen. 5-Minuten-Open-Time-Kerzen, Close-Time-Renditen, drei SOL-/BTC-Lags, B1/M1 unpenalisiert, Refit Apr/Mai/Juni, Nulllabels vorab festgelegter Score-Maske zuordnen. Alle Testprognosen müssen vor Zielmaskierung entstehen. Test-Ende ist exklusiv.

## Festgelegte drei synthetische Szenarien
1. **Null I (unabhängig):** BTC-Renditen unabhängig von der zukünftigen SOL-Richtung; Vorzeichen der SOL-Innovationen i.i.d. symmetrisch. ETH wird nur der Datenform wegen erzeugt.
2. **Null II (gemeinsames Risiko):** BTC/SOL teilen einen persistenten stochastischen Volatilitätsfaktor und positive *gleichzeitige* Innovationskorrelation. SOL-Vorzeichen sind jedoch konditional auf jede abgeschlossene historische SOL/BTC-Information symmetrisch und unabhängig. Deshalb gibt es keinen echten Zusatznutzen der letzten BTC-Renditen für die nächste SOL-*Richtung*. Dies ist **keine** Nullhypothese für die Volatilitätsprognose.
3. **Alternative (schwache Richtung):** Gleiche Faktoren wie Null II, aber der SOL-Return enthält zusätzlich einen **festen** Term proportional zur vorherigen BTC-Innovation. Damit ist tatsächliche gerichtete Prognoseinformation konstruktiv eingebaut. Deren realisierte Log-Loss-Effektgröße wird berichtet; nicht nachträglich auf einen Wunscheffekt justiert.

## Vorregistrierte Simulationseinstellungen
- Szenarien 1/2/3 mit je **200 unabhängigen Replikationen** (600 insgesamt). Seeds deterministisch: `20261114000 + 1000*szenario_index + replikations_index`.
- Einmalsimulation mit vollumfänglichem 5-Minuten-Gitter und Monatsrefits pro Replikation. **Keine Wiederverwendung einer trainierten Modellspezifikation aus einer anderen Replikation.**
- Kontrollrechnung: auch B0-Log-Loss, Mittelwert B1 und M1, beobachtete Nullrenditen, Zahl der Prognosen und Zahl der für das Scoring verwendeten Targets dokumentieren.
- 7-Tage gepaarter Kalenderblockbootstrap, 5.000 Ziehungen/Replikation. Für Rechnerressourcen nur eine Replikation gleichzeitig, `OPENBLAS_NUM_THREADS=1` und `OMP_NUM_THREADS=1`. Dies reduziert Threads, nicht das statistische Prüfprotokoll.
- Pro Nullszenario Anteil positiver Gate-Entscheidungen und exaktes 95%-Binomialintervall (Clopper-Pearson); für Alternative Trefferanteil als Power-Schätzung mit 95%-Binomialintervall. Nicht nur Punktschätzungen ausgeben.
- Ziel/Orientierung: Fehlalarmrate von nominal 5%. **Nicht** als bestanden ausgeben, nur weil die beobachtete Fehlalarmrate unter 5% liegt. Die Unsicherheit bei 200 Replikationen muss begründet bewertet werden; im Zweifel „ungeklärt“.
- Technische oder numerische Modellfehler: FAIL-CLOSED, genaue Fehlermeldung/Seed speichern. Keine stillen Ersatzfits und kein automatisches Retuning.
- Keine neue R8-B-Modellsuche. Keine Rückwirkung auf registriertes R8-Protokoll. Offene Leistungs-/Kalibrierungsfragen können zu einer später versionierten Änderung **vor** einem Blindtest führen.

## Durchführungsgates
- Vor dem 600er Hauptlauf: eigenständiger Review der synthetischen DGP, ihrer **bedingten** Nullhypothesen, des Bootstrap-Vertrags und der Labelverfügbarkeit.
- Erst danach separat versioniertes Skript auf synthetischen Daten (Smoke-Test zulässig, aber nicht zur wissenschaftlichen Schlussfolgerung nutzen).
- Ergebnisse, Versionen, Seeds, Originalcode-Hashes und negative/abgebrochene Läufe archivieren. Keine produktiven TradingLab-/Freqtrade-Dateien anfassen.
- **Phase-C-Freigabe bleibt NEIN.** Ein bestandener Techniktest oder eine niedrige simulierte Fehlalarmrate allein ist keine vollständige Zulassung.

## Fachbezug
Clark & West (2007), nested forecast comparisons, DOI 10.1016/j.jeconom.2006.05.023; Giacomini & White (2006), predictive ability under specified estimation procedures, DOI 10.1111/j.1468-0262.2006.00718.x. Diese Arbeiten ersetzen nicht die hier notwendige empirische Größen-/Power-Kalibrierung der tatsächlich verwendeten Logit-Refit-Prozedur.
