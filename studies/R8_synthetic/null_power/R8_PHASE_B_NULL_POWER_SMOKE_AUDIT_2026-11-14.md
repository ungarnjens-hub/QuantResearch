# R8-B – Vorabprüfung des Null-/Power-Kalibrierungsmoduls

**Datum:** 2026-11-14  
**Status:** TECHNISCHER SMOKE-TEST BESTANDEN; statistische Kalibrierung NICHT durchgeführt; Phase C NO-GO.

## Provenienz
- Design: `R8_PHASE_B_NULL_POWER_PRUEFPROTOKOLL_2026-11-14.md`.
- Neuer Kalibrierungscode: `R8_phase_b_null_power_kalibrierung.py`.
- Unveränderte eingebundene E2E-Prognosepipeline `R8_phase_b_synthetischer_e2e_test.py` SHA-256 `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff`.
- Smoke-Test in gesondertem Ausgabeordner auf ausschließlich synthetischen 5-Minuten-Preisreihen. Lokale Python-Versionen der technischen Prüfumgebung unterscheiden sich möglicherweise von der Nutzerumgebung, daher Bibliotheksversionen und Laufzeit bei Wiederholung protokollieren.

## Tatsächlich ausgeführte Prüfungen
1. `--preflight`: drei Datengeneratoren liefern endliche positive Preise auf lückenlosen 5-Minuten-Rastern. PASS.
2. `--smoke`: ein kompletter Durchlauf je Szenario durch die **unveränderten** Funktionen für Merkmale, zeitliches Training, unpenalisierte Logit-Prognose, Nullrenditen-Maske, Log-Loss und 7-Tage-Blockbootstrap (5.000 Ziehungen). PASS.

## Smoke-Ergebnisse (je n=1: keine Inferenz über Fehlalarm oder Power)

| Synthetisches Szenario | Positive Gate-Entscheidung | Mittlerer absoluter Log-Loss-Vorteil |
|---|---:|---:|
| BTC unabhängig | Nein | -0,00002667 |
| Gemeinsame Volatilität, kein bedingter Vorzeichen-Zusatznutzen | Nein | +0,00004379 |
| Künstlicher BTC-Vorlaufeffekt | Ja | +0,01215006 |

**Wichtig:** Das ist exakt **eine** Realisation pro Szenario. Die Fallzahlen sind nicht geeignet, eine Fehlalarmrate oder Power abzuleiten. Insbesondere darf die alternative künstliche Effektstärke nicht rückwirkend als kalibrierter 1–2%-Effekt bezeichnet werden.

## Fachliche Freigabesperren
- Die bedingte Nullhypothese der gemeinsamen Volatilitätswelt ist logisch plausibel konstruiert, muss aber **vor** dem Hauptlauf unabhängig auf mögliche Leakage- und Konditionierungsprobleme auditiert werden.
- Das neue Prüfskript ist **kein Bestandteil der früher eingefrorenen R8-Versionen**. Erst eigener Commit/Hash, anschließendes unabhängiges Review und Freigabe.
- Geplant: 200 unabhängige Replikationen je Szenario mit exakten Binomial-Konfidenzintervallen; noch **nicht ausgeführt**.
- Die Bootstrap-Inferenz ist auch bei 600 Replikationen nur für die spezifizierten künstlichen Datenprozesse kalibriert, nicht universell.
- `sklearn` war in dieser technischen Prüfumgebung Version 1.8.0; auf dem Nutzerrechner ist 1.9.1 installiert. Die API und Fit-Konvergenz beim getrennten Prüflauf kontrollieren. Deprecation-Warnungen sind keine inhaltlichen Freigaben.
- Original-R5/R6, R7, Freqtrade und Paper-Bots bleiben unberührt.

**Entscheidung: Phase B weiter; Phase C gesperrt.**
