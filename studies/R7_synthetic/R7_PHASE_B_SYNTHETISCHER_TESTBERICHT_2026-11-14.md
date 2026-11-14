# R7: Synthetisches Phase-B-Prüfgate

Datum: 2026-11-14. **Status: Teilprüfungen bestanden, keine Phase-C-Freigabe.**

## Prüfgrundlage

- Registrierte R7-Dokumente: `R7_FORSCHUNGSDESIGN_PRAEZISIERT_2026-11-14.md`, `R7_FACHAUDIT_B2_M2_2026-11-14.md` und `R7_PHASE_B_KORREKTUREN_UND_FREIGABEGATES_2026-11-14.md`.
- Ausführung ausschließlich mit **synthetisch erzeugten** Daten in einem getrennten Prüfskript. Keine Rohmarktpreise, API, produktive TradingLab-Dateien oder Paper-Bots verwendet.
- Reproduktionsartefakte: `R7_synthetisches_phase_b_gate.py`, `R7_phase_b_synthetik_resultat.json`.  Zufallsseed `20261114` (Szenarien mit expliziten abgeleiteten Seeds); NumPy, pandas und SciPy erforderlich. **Dies ist kein unabhängiges zweites Implementierungs-Audit.**

## 1. Technischer End-to-End-Plausibilitätstest: PASS im getesteten Umfang

Drei künstliche 5-Minuten-Kursserien (BTC/ETH/SOL), logarithmische Renditen, eigene HAR-Fenster 12/288/2016, ETH-Ziel `log(sum(next 12 squared returns)+1e-12)`, B2 und M2 mit Intercept, monatliche expandierende OLS-Refits mit Verfügbarkeitsfilter:

| Monat | Trainingszeilen | Prognosen |
|---|---:|---:|
| Januar 2027 | 10.055 | 744 |
| Februar 2027 | 10.799 | 672 |
| März 2027 | 11.471 | 743 |
| **Gesamt** | | **2.159** |

- Zeitkonvention: letzte bekannte Kerze Open-Time `hh:55`, Informationszeit `hh+1:00 UTC`, Labelzeit frühestens `t+65 min`; Forecast nur, wenn Label bis zum Testende verfügbar.
- Vollständige erwartete Forecast-Achse und endliche Werte: **PASS**. Fehlender synthetischer Zeitstempel wird beim einfachen Frequenzcheck erkannt.
- Modellmatrix auf synthetischen Fällen vollen Ranges: **PASS**. Zukunftsänderung an ETH-Kursen verändert das bereits berechnete ETH-HAR-Merkmal zum Beobachtungszeitpunkt nicht: **PASS**.

**Grenze:** Für Datenprovenienz, echte Lücken-/Duplicate-/OHLC-Validierung, Konditionsschwellen und vollständige Störungstests liegt noch kein produktionsnaher, separat eingefrorener R7-Runner vor. Ein bestandener Plausibilitätstest ist keine vollständige technische Freigabe.

## 2. Synthetische Monte-Carlo-Kalibrierung: Vorprüfung, KEINE finale Inferenzfreigabe

**Design:** 240 unabhängige künstliche Simulationen je Szenario. Stündliche, korrelierte prädiktive Variablen (ETH 3, SOL 3, BTC 3), persistenter gemeinsamer Faktor und AR(1)-Prognoserest, 365 Tage Anfangstraining, 90 Testtage, monatliche expandierende Schätzung von B2/M2, 2 Stunden Label-Sicherheitsabstand. Gepaarte 7-Tage-Moving-Block-Bootstrap-Intervalle, **400 Ziehungen je Simulation**; Tages-HAC mit 7 Lags ergänzend. Dies ist **nicht** die endgültig geplante Monte-Carlo-Prüfung unter einem realistischeren 5-Minuten-HAR/RV-Datengenerierungsprozess.

| Szenario | Simulationen | Untere 95%-Bootstrap-Grenze > 0 | Positive MSE-Punktschätzung | Mittelwert Gewinn |
|---|---:|---:|---:|---:|
| H0: BTC-Koeffizient = 0 | 240 | **1/240 = 0,42 %** | 32,08 % | −0,041 % |
| H1: künstlicher BTC-Koeffizient = 0,35 | 240 | **240/240 = 100 %** | 100 % | +20,50 % |

**Einordnung:** In dieser konkret simulierten Null-Situation sah das vorläufige Kriterium konservativ aus. Wegen nur 240 Replikationen ist die Fehlalarmrate unpräzise geschätzt; die 100%-Erkennung betrifft eine **sehr starke** künstliche Alternative und darf nicht auf den R5/R6-Effekt von rund 1–2 % übertragen werden. Außerdem sind je Simulation nur 400 statt 5.000 Bootstrap-Ziehungen verwendet worden. Weder allgemeine Testgröße noch Konfidenzintervall-Abdeckung sind damit ausreichend kalibriert.

## 3. Präzise offene Gates

1. Realistischer synthetischer 5-Minuten-Volatilitätsprozess, der die HAR/RV-Erzeugung, drei korrelierte Märkte, bedingte Heteroskedastizität und reale monatliche Refit-Logik in **jeder** Monte-Carlo-Replikation integriert.
2. Null-Kalibrierung einschließlich Fehlspezifikation, schwachen Alternativen von ungefähr 1–2 % MSE, mehrerer Abhängigkeitsgrade und ausreichend vieler Replikationen; 5.000 Bootstrap-Ziehungen für finale Regel oder vorher begründete neue Spezifikation.
3. Entscheidung über das exakte finale Inferenz-Gate und seine Fehlerkontrolle vor Ergebniszugriff. Clark–West nur als vorher registrierte Sekundärdiagnostik, nicht opportunistisch.
4. Separat fixierte Fehlerbehandlung: Rang-/Konditionsprüfung, unzulässige 5-Minuten-Intervalle, Lücken, Duplikate, fehlende Marktdaten, erwartete Informationszeiten, NaN/Inf, Szenarien mit nicht genügend Trainingszeilen.
5. Prüfung des Forschungsregisters und der Datenprovenienz. Januar–März 2027 ist am Berichtsdatum zukünftiger Zeitraum: **keine vorzeitige Teilmessung**.

## Gesamtentscheidung

**Phase B bleibt offen, Phase C bleibt NO-GO.** Ein technischer synthetischer Durchstich und eine erste Inferenz-Plausibilisierung sind gelungen. Daraus folgt weder eine formale Validierung der Testgröße noch ein neuer empirischer Marktmechanismus. R5/R6 bleiben unangetastet.
