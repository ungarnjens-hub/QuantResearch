# R8 Phase B: v2 Sicherheits- und Fehleraudit

**Datum:** 14.11.2026  
**Ergebnis:** Die zwei technischen Sperren des vorherigen Audits wurden in einer **neuen, separaten Skriptversion** umgesetzt und synthetisch geprüft. **KEINE Freigabe des 600er-Hauptlaufs oder von Marktdaten.**

## Unveränderte Ausgangslage
- Original-Kalibrierungsrunner: `R8_phase_b_null_power_kalibrierung.py`, SHA-256 `f2cd2d3700a23b14b2fc5b424347c0fbebfc116101d078895d58ae3075fd4975`.
- Unveränderte synthetische Forecastpipeline: `R8_phase_b_synthetischer_e2e_test.py`, SHA-256 `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff`.
- Neuer Wrapper: `R8_phase_b_null_power_kalibrierung_v2.py`, SHA-256 `c67ded5c5d2812d20608ad9508ad6c6dc4d3efbee9708dbaa09dfa5ab67fe6f9`.
- Vorregistriertes Prüfprotokoll und alle statistischen Features/Parameter bleiben unangetastet.

## Implementierte Schutzmaßnahmen

**A: Gesperrter Hauptlauf.** `--run` verlangt eine **gesonderte, versionierte** JSON-Freigabedatei über `--approval-file` mit `approved=true`, exakt begrenztem Scope `R8_B_SYNTHETIC_600_ONLY`, SHA-256 des Forecast-Quellcodes, des Prüfprotokolls und der neuen Skriptdatei sowie `repetitions_per_scenario=200`. Abweichung oder fehlende Freigabe: Abbruch **vor** Modellladen und Ergebnisverzeichnis. `--smoke`, `--preflight` und `--selftest-gates` erlauben keine stillschweigende Hauptlauf-Freigabe. Diese Datei ist **nicht** Teil des Pakets.

**B: FAIL-CLOSED-Fehlerarchiv.** Bei einer Exception in einer Simulationsreplikation wird `FAILURE.json` mit Szenario, Seed, Replikationsindex, Fehlertyp, Fehlermeldung, vollständigem Traceback sowie Runner-, Protokoll- und Forecast-Hashes atomar geschrieben. Fehlversuch wird nicht als bestanden ausgegeben, es entsteht keine Erfolgs-`summary.json`. Ergebnisse werden nicht überschrieben; jedes Ausführungsverzeichnis muss neu sein.

**Hinweis zur Dauerhaftigkeit:** Atomarer Dateiaustausch plus `fsync()` der Fehlerdatei, aber keine Zusage zu Hardware-Ausfällen oder Verzeichnismetadaten nach Stromverlust. Ein Python-Absturz außerhalb der Replikationsschleife wird nicht in jedem Fall mit Seed dokumentiert. Deshalb ist noch ein unabhängiger Fehlerpfad-Audit erforderlich.

## Tatsächlich ausgeführte lokale Tests

- Python-Syntaxkompilierung: **PASS**.
- `--run` ohne Freigabe: **abgelehnt vor dem Modellfit**, keine Ausgabedateien angelegt.
- Fehlende Freigabedatei: **abgelehnt**.
- `--selftest-gates`: **PASS**. Eine simulierte `ValueError("INJECTED_FAILURE")` wurde im Fehlercheckpoint mit Szenario `independent_null` und Seed `20261114000`, Fehlerklasse, Traceback und Codehash gesichert; kein Success-Summary.
- `--preflight`: alle drei synthetischen DGP-Szenarien **PASS**, ohne Modelle zu schätzen.

## Grenzen und Entscheidung

**PASS** für die beiden implementierten Schutzmechanismen im geprüften Umfang.

**NO-GO** für den 600er-Hauptlauf. Vor Freigabe erforderlich: unabhängiger Review der v2-Datei, reproduzierbarer Ein-Replikations-Leistungs- und Versionscheck, separater dokumentierter Freigabeakt sowie erneute Sicherheitsprüfung der Implementierung. Danach erst exakt vorregistrierte 200+200+200 Replikationen. Keine Zielmarktprognosen, kein Zugriff auf Binance-Daten, keine Handelsstrategie.

**R8 Phase C:** weiterhin **NICHT FREIGEGEBEN**.
