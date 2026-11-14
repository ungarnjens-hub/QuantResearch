# R9 Phase B – gebündelter Daten- und Synthetik-Audit
**Datum:** 14.11.2026  
**Bezug:** R9 Phase A (`7bfbd53`), R9 Phase B Methodenaudit (`5c14cd3`)

## Auditentscheidung
**Nur technische Vorbereitung. Phase C weiterhin nicht freigegeben.** Keine echten Ereignis-/Rendite-/PnL-Messungen.

## Gelieferter Runner
`R9_phase_b_kombinierter_audit.py`:
- prüft Binance-USD-M-Perpetual-Metadaten, CSV-unabhängige Parquet-Hashes, UTC-Raster, 35.424 Kerzen, OHLCV, Duplikate und das marktübergreifende Zeitraster **ohne** reale Renditen zu bilden;
- setzt den vorregistrierten Ereignisindex für synthetische Arrays mit 288 **vor dem Impuls abgeschlossenen** Vergleichsrenditen, sechs Impulskerzen, sechs Zukunftskerzen um;
- testet die gemeinsame sechs-Zeitpunkte-Sperre für ausgewählte Ereignisse, fehlende/ungültige Preise und Nullvolatilität;
- testet gepaarten, kreisförmigen 7-Tage-Kalendertags-Blockbootstrap mit bekannter Differenz und leeren Vergleichsgruppen;
- beendet sich mit Exit-Code 2 bei Auditfehler.

## In dieser Umgebung tatsächlich ausgeführte Tests
11/11 technische Synthetik-Tests **PASS** (lokal NumPy 2.3.5, pandas 2.2.3); echte Benutzerdateien konnten hier nicht gelesen werden und wurden **nicht** gemessen. Der Nutzer muss den kombinierten lokalen Runner einmalig mit der R9-Forschungsvenv ausführen. Der Test validiert keine Nulltest-Kalibrierung über verschiedene realistische Autokorrelations-/Regimeprozesse und keine Fähigkeit, kleine echte Effekte nachzuweisen.

## Offene methodische Gates
1. **Statistische Mindestpräzision:** vor Markt-Renditemessung Mindestzahl Ereignisse je Gruppe/Markt und Mindest-Effektgröße auf vorab festgelegter Skala definieren.
2. **Nullkalibrierung/Mehrfachtest:** gepaarte Moving-Block-Bootstrap-Perzentil-KIs sind keine vollständig definierte p-Wert-Prozedur. Keine Signifikanzbehauptung/Holm ohne passende kalibrierte Nulltestmethode.
3. **Datenverbrauch:** Juli–Oktober 2026 sind als schon analysierter historischer Bestand gekennzeichnet. R7 Jan–März 2027 sowie R8-B Apr–Juni 2027 nicht umwidmen. Einen geeigneten zukünftigen, nicht für andere Forschung reservierten R9-Blindtest nur per eigener Registrierung zuweisen.
4. **Interpretation:** M1/B1 sind potenziell nach Impulsstärke, Liquidität und Tageszeit verschieden. Primäres Delta ist ein unadjustierter Gruppenvergleich, kein Nachweis, dass Volumen kausal wirkt.
5. **Wirtschaftlicher Wert:** Der vorregistrierte Close-to-Close-Zukunftsertrag ist kein handelbarer PnL. Späterer Einstieg erst nach Impulsschluss; Gebühren, Spread, Slippage, Funding und Risikobeschränkungen müssen gesondert fixiert werden.

## Akzeptanz
- Lokal `R9 PHASE B SYNTHETIK: PASS` und `R9 DATENINVENTAR: PASS` erforderlich.
- Auch bei zwei PASS bleibt `R9 PHASE C: NOT APPROVED`.
- **Keine** automatische Marktmessung nach den Audits; dies ist ein bewusster Sicherheits- und Forschungsstandard.

## Quell- und Laufzeitgrenzen
Der Runner ist Python-only, fordert keinen Netzwerkzugriff und schreibt nicht in produktive Verzeichnisse. Die Parquet-Daten und das Manifest müssen vor Ort unverändert vorliegen. Quellen-Hashes aus dem R8-Inventar werden erneut kontrolliert.
