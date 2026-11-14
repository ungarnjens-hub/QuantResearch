# R8 – Phase-B: synthetischer End-to-End-Selbsttest

Datum: 14.11.2026  
Status: **Teilprüfung bestanden; Phase C weiterhin NO-GO**.  
Bezugsdokument: `R8_PHASE_A_NACHTRAG_V02_2026-11-14.md`; Vorgänger-Audit Git-Commit `a7f2a19`.

## Prüfgegenstand

Künstliche, reproduzierbar erzeugte 5-Minuten-Schlusskurse für BTC, ETH und SOL. Testpipeline verarbeitet UTC-Kerzen-Öffnungszeiten, wandelt diese in die Verfügbarkeit nach Kerzenschluss um, bildet drei abgeschlossene SOL-/BTC-Rendite-Lags, prognostiziert das Vorzeichen der nächsten SOL-Rendite mit unpenalisierter logistischer Regression B1/M1, führt monatliche Refits aus und berechnet Log-Loss sowie Tagesblockbootstrap. **Keine realen Marktdaten gelesen, keine produktiven Systeme angefasst.**

## Ausführung / Versionen

- Skript: `R8_phase_b_synthetischer_e2e_test.py`
- Skript-SHA256: `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff`
- NumPy `2.3.5`, pandas `2.2.3`, scikit-learn `1.8.0`; Seed `20261114`.
- Aufruf: `OPENBLAS_NUM_THREADS=1 python R8_phase_b_synthetischer_e2e_test.py R8_phase_b_synthetischer_e2e_resultat.json`
- Scikit-learn 1.8 signalisiert eine **Deprecation-Warnung** für `penalty=None`; die Schätzkonfiguration und eine künftig unterstützte äquivalente, unpenalisierte API müssen vor produktionsunabhängiger Messfreigabe versioniert und gegengeprüft werden.

## Synthetische Zeitachse und Ergebnisse

| Größe | Ergebnis |
|---|---:|
| Trainingskerzen 2025-01 bis 2026-12 | 210,240 |
| Synthetische Testkerzen 2027-04 bis 2027-06 | 26,208 |
| Generierte OOS-Prognosen | 26,204 |
| Bewertete Prognosen mit nichtnulligem SOL-Ziel | 25,934 |
| Ausgeschlossene Nullrenditen (nach Vorhersage) | 270 |
| Log-Loss B0, nur synthetisch | 0.693149181 |
| Log-Loss B1, nur synthetisch | 0.693155695 |
| Log-Loss M1, nur synthetisch | 0.693161880 |
| Differenz B1–M1, nur synthetisch | -0.000006185 |
| 95%-Tagesblock-Bootstrapintervall, synthetisch | [-0.000023164, +0.000005997] |

Die künstliche Nullwelt erzeugte hier **keinen positiven Prognosebefund**. Dieses Einzelergebnis ist **keine empirische Fehlalarmkalibrierung**. Wiederholte unabhängige synthetische Nullreplikationen wurden in dieser Ausführung ausdrücklich **nicht** vorgenommen.

## Refit- und Zeitgrenzen

| Refit | Training (nach Nullmaskierung) | Prognosen | Erste Prognose |
|---|---:|---:|---|
| 2027-04-01 | 208,069 | 8,636 | 2027-04-01 00:20 UTC |
| 2027-05-01 | 216,616 | 8,928 | 2027-05-01 00:00 UTC |
| 2027-06-01 | 225,452 | 8,640 | 2027-06-01 00:00 UTC |

Die Datenerzeugung enthält **keine** Kerzen aus `2027-01-01` bis `2027-04-01`. Die drei Refits nutzen ausschließlich vor dem jeweiligen Refit vorhandene Trainings-Labels. Zur ersten April-Prognose sind nach dem Neustart des Zeitrasters drei vollständige vergangene Renditen nötig; erster zulässiger Entscheidungszeitpunkt **01.04.2027, 00:20 UTC**. Der Zeitpunkt `2027-01-01 00:00 UTC` kann der letzte *bekannte Schluss* einer historischen 2026er Kerze sein, ohne dass ein 2027er Intervall zum Training verwendet wird.

### 11 bestandene deterministische Checks

- `open_time_to_close_time`
- `latest_complete_feature`
- `target_next_closed_candle`
- `label_known_only_next_close`
- `3_lags_require_history`
- `zero_label_is_NA_not_negative`
- `missing_candle_rejected`
- `duplicate_rejected`
- `naive_time_rejected`
- `only_one_class_rejected`
- `constant_feature_rejected`

## Während der Selbstprüfung korrigierte technische Fehler

1. Ein initialer Test erwartete irrtümlich, dass die letzte *Close-Time* des Trainings **vor** dem Trainingsende liegt. Die letzte historische Open-Time `2026-12-31 23:55 UTC` schließt exakt `2027-01-01 00:00 UTC`. Testbedingung korrigiert; Trainingslabels werden nach ihrem gesonderten Verfügbarkeitszeitpunkt gefiltert.
2. Ein initialer Test zählte das notwendige Warm-up um eine Beobachtung zu hoch. Nach dem ersten `diff()`-Return fehlen noch **zwei** zurückliegende Renditen für drei Lag-Spalten. Danach muss zusätzlich die letzte unbeobachtbare zukünftige Zielrendite ausgeschlossen werden. Erwartungszahl korrigiert und erfolgreich reproduziert.

Die beiden Fehlversuche sind **nicht** als bestandene Läufe gezählt; hier berichtet sind die Ergebnisse des final ausgeführten Skripts.

## Wesentliche noch offene Auditsperren

- **Null-Fehlalarmkalibrierung mit wiederholten unabhängigen, realistisch abhängigen Datenprozessen** und vollständigem HAR-fremden R8-Logit-Walk-Forward ist noch ausstehend. Die 5.000 Bootstrapziehungen innerhalb eines einzelnen Tests ersetzen das nicht.
- **R8-A:** Ein eigenständiger synthetischer Datenqualitäts- und Korrelations-/Vorzeichen-/Bootstrapcheck für alle drei Paare muss noch umgesetzt werden. Das aktuelle Skript implementiert **nur R8-B**, nicht die R8-A-Auswertung.
- Bootstrap mit Randtagen, Ausfällen und ungleicher Tageszahl wurde in diesem Test nicht adversarial abgeprüft. Ein Nullrenditenanteil wurde geprüft, nicht jede mögliche Kombination fehlender Tage.
- Die numerische Stabilität und Fail-Closed-Erkennung bei Separation, Quasi-Separation und Solver-Warnungen ist nicht vollständig abgesichert; bloßes Prüfen von `n_iter_` genügt nicht.
- Exakte Boundary-/Latenzregel, ob eine **exakt** zum Refit-Zeitpunkt geschlossene letzte Trainingskerze technisch schon verfügbar ist, bleibt gesondert festzulegen. Synthetisch wurde `label_available_at <= refit` verwendet.
- Das langfristige Forschungsregister für alle früheren Untersuchungen, Datenprovenienz und Unverbrauchtheit eines späteren Testzeitraums muss vor Phase C gesondert geprüft werden.

## Entscheidung

**Technischer E2E-Grundpfad: PASS im geprüften synthetischen Umfang.**  
**Gesamtes R8-Phase-B-Gate: NO-GO**, bis die oben genannten Punkte geschlossen sind.  
Keine Markt- oder Profitabilitätsbehauptung aus synthetischen Log-Loss-Zahlen. R4–R7 bleiben unverändert. Dieses Audit ist vor einer echten Datenauswertung zu archivieren.
