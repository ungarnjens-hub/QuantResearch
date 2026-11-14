# R8-B – Unabhängiges Audit der synthetischen Null-/Power-Kalibrierung

**Datum:** 14.11.2026  
**Status:** **BEDINGT FACHLICH PLAUSIBEL, TECHNISCHES NO-GO FÜR 600 HAUPTLÄUFE**  
**Umfang:** Quelltext- und Vertragsprüfung, keine neuen Marktmessungen und keine 600 Simulationen. Befunde beziehen sich ausschließlich auf die im Archiv gespeicherten Dateien; der auf dem Nutzerrechner installierte Versionsstand wurde nicht selbst ausgeführt.

## Geprüfte Originaldateien

- `R8_PHASE_B_NULL_POWER_PRUEFPROTOKOLL_2026-11-14.md`
- `R8_phase_b_null_power_kalibrierung.py` (SHA-256 `f2cd2d3700a23b14b2fc5b424347c0fbebfc116101d078895d58ae3075fd4975`)
- `R8_phase_b_synthetischer_e2e_test.py` (SHA-256 `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff`)
- `R8_PHASE_B_NULL_POWER_SMOKE_AUDIT_2026-11-14.md`

## 1. Prüfung des künstlichen Datenprozesses

**Null I: plausibel gültig.** Die BTC- und SOL-Innovationen werden getrennt erzeugt. Die SOL-Richtung ist zum Zeitpunkt vor der künftigen Innovation symmetrisch. Der deterministische Nullrendite-Maskenindex `::97` nutzt nicht den künftigen Innovationswert. Es besteht kein konstruktiv eingebrachter BTC-Zusatznutzen für das nächste SOL-Vorzeichen.

**Null II: plausibel gültig für eine *bedingte Richtungsnull*.** Der AR(1)-Logvolatilitätsfaktor ist persistent, der Multiplikator `exp(shared)` stets positiv. Die zeitgleich korrelierten BTC-/SOL-Innovationen (`rho=0.65`) teilen die SOL-Richtung des aktuellen Intervalls; zum nächsten Intervall bleiben die neuen SOL-Innovationen jedoch unabhängig und symmetrisch. Historische BTC-Information kann hier die *Volatilität* vorhersagen, nicht per Konstruktion das nächste SOL-*Vorzeichen*. Das gilt nur für den exakt implementierten DGP, nicht als Aussage über reale Märkte.

**Alternative: plausibel gerichteter Zusatznutzen.** Der Term `0.20 * ebtc[t-1]` beeinflusst SOL bei `t` und stammt aus einer zeitlich früheren BTC-spezifischen Innovation, die in `BTC[t-1]` anteilig beobachtbar ist. Die Effektgröße ist *nicht* auf 1–2 % kalibriert und darf nicht so beschrieben werden.

**Replikationen:** Für jedes Szenario wird ein separater `default_rng(seed)` erstellt. Seeds unterscheiden sich deterministisch. Die Pseudozufallsströme gelten im üblichen Simulationssinn als separat reproduzierbare Replikationen; mathematisch beweisbare Unabhängigkeit der Generatorströme wird damit nicht nachgewiesen. Sowohl Historie als auch Testfenster werden pro Replikation mit demselben Generator sequentiell erzeugt.

## 2. Geprüfter Forecast- und Inferenzvertrag

- Referenz-Forecastcode wird mit festem SHA-256 geladen, einschließlich `build`, `training_rows`, `fit_predict`, `score`, `bootstrap`: **PASS im Quelltext**.
- Original-Training 2025-01 bis 2027-01, reserviertes R7-Fenster 2027-01 bis 2027-04, Test 2027-04 bis 2027-07: **PASS im Quelltext**; es werden keine künstlichen Preise im Sperrfenster erzeugt.
- Monatliche Refits (April, Mai, Juni), Labels nur bis zum Refit bekannt: **PASS im Quelltext**.
- 26.204 erwartete Prognosen, Ziel-Nullrenditen erst nach Prognose maskiert, 7-Tage-Blockbootstrap, 5.000 Ziehungen mit festem Seed: **PASS im Quelltext**.
- Exakte Clopper-Pearson-Binomialintervalle sind formal korrekt programmiert; ihre fachliche Interpretation muss einschließlich begrenzter Präzision bei n=200 erfolgen.
- Die feste Bootstrap-Zufallsfolge innerhalb aller Replikationen reduziert Monte-Carlo-Streuung bei Vergleichen, garantiert aber keine allgemeine Testgrößenkontrolle. Inferenz bleibt für die spezifischen DGPs zu kalibrieren.

## 3. Verbindlich zu behebende Sperren

**Sperre A – explizite Hauptlauf-Freigabe fehlt.** Das Skript erlaubt bereits `--run` mit `--source` und `--output-dir`, ohne eine separate Phase-B-Auditfreigabe zu prüfen. Der Kommentar „subject to approval“ ist kein technisches Schutzgate. Der nächste Hauptlauf muss vorab an eine *eigenständig versionierte* Freigabedatei mit Protokoll- und Skripthash sowie bestätigter expliziter Zustimmung gebunden werden. Der bisherige Quelltext bleibt unverändert archiviert; Verbesserung nur in einer neuen Datei/Version.

**Sperre B – Fehlerprotokoll unvollständig.** Bei Exceptions innerhalb `simulate()` wird der aktuelle Seed nicht garantiert in einer eigenen Fehlerdatei hinterlegt, obwohl das Protokoll genau das verlangt. Ein bereits angelegter Ergebnisordner und ein Python-Traceback reichen als vollständige evidenzsichere Fehlererfassung nicht aus. Vor dem Hauptlauf muss ein `FAIL-CLOSED`-Fehlercheckpoint mit Szenario, Seed, Fehlertyp, Traceback, Quellcodehash und Abbruchstatus atomar geschrieben werden.

**Sperre C – Kalibrierungsstatus begrenzen.** Ein einzelner Smoke-Lauf pro Szenario beweist keine Fehlalarmrate oder Power. Bei 200 Replikationen je Nullszenario können die Clopper-Pearson-Intervalle relevante Unsicherheit enthalten. Kein allgemeines Gütesiegel allein bei unter 5 % beobachteter Rate.

**Sperre D – Ressourcen-/Versionsgate.** Die reale Umgebung verwendet Python 3.14, scikit-learn 1.9.1; Smoke-Archiv nennt 1.8.0. Die neue Version ist noch nicht im vollen Kalibrierungscode nachgewiesen. Ein separater, vorregistrierter Laufzeit- und Speichercheck für *eine* vollständige Replikation ist vor dem 600er-Lauf nötig. Performanceoptimierungen dürfen Prognosefunktion, Bootstrap oder Statistik nicht verändern.

## 4. Entscheidung und Abnahmekriterien

**FACHLICH:** Die konditionalen Nullwelten und die eingebaute zeitgerichtete Alternative sind für den *geplanten synthetischen* Forschungszweck plausibel. Kein offensichtlich konstruierter Look-ahead im Datenprozess gefunden.

**TECHNISCH:** **NO-GO für den 600er-Lauf**, bis A und B behoben und auf synthetischen Fehlerszenarien getestet sind; C und D dokumentiert wurden. Keine 600 Simulationen ausführen und keine realen Kursdaten messen. Bereits versionierte Skripte, R5–R7 und TradingLab bleiben unangetastet.

**Nächste erlaubte Arbeit:** Eine neue `v2` des Kalibrierungswrappers isoliert erstellen, nur Freigabe- und Fehlercheckpointing ergänzen, mit synthetischem absichtlich ausgelöstem Fehler demonstrieren; dann erneut unabhängig auditieren. Bestehende Versionen nicht überschreiben und Ergebnisse nicht optimieren.
