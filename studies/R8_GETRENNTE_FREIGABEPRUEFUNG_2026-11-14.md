# R8 – Getrennte Freigabeprüfung R8-A / R8-B
**Datum:** 14.11.2026  
**Status:** Methodisches Entscheidungsgutachten, keine Marktdatenmessung, kein neuer Simulationslauf.

## Prüfbasis
- `R8_KORRELATION_UND_LEADLAG_PHASE_A_2026-11-14.md`
- `R8_METHODENAUDIT_PHASE_B_2026-11-14.md`
- `R8_PHASE_A_NACHTRAG_V02_2026-11-14.md`
- `R8_PHASE_B_KORRELATION_SYNTHETIK_AUDIT_2026-11-14.md`
- R8-B: archivierter synthetischer 600er-Abschluss (Commit `7f16374`), Ausgaben der Nutzerkonsole.

## A: Gleichzeitige Korrelation – **BEDINGTES GO FÜR REIN DESKRIPTIVE MESSUNG**
**Frage:** Wie stark sind die zeitgleichen 5-Minuten-Logrenditen BTC–ETH, BTC–SOL und ETH–SOL im vorregistrierten Zeitraum August–Oktober 2026 korreliert?

**Fachliches Gate bestanden:** Es sind exakt drei Paare, ein fixer historischer Zeitraum (2026-08-01 bis 2026-11-01 exklusiv), eine gemeinsame Stichprobe, Pearson-Korrelationen, eine feste Nullrendite-Policy für Vorzeichenvergleich und ein 7-Tage-Blockbootstrap (5.000 Resamples, Seed 20261114) registriert. Synthetische Implementierung: 18/18 technische Prüfpunkte bestanden.

**Vor dem ersten Messzugriff noch zwingend auszuführen:** 
1. Lokal vorhandene Rohdateien **nur lesend** lokalisieren und ihre Börse, Markttyp, Preisart und 5-Minuten-Open-Time prüfen; ein R5/R6-Volatilitäts-Forecast-CSV ist **kein** Ersatz für drei Rohpreisreihen.
2. Vor-Schlusskurs für die erste Rendite nachweisen: 2026-07-31 23:55 UTC Open-Time (Kurs bis 2026-08-01 00:00 UTC geschlossen), anschließend 2026-08-01 00:00 bis 2026-10-31 23:55 UTC. Exakt 26.497 erforderliche Schlusskurse pro Markt, 26.496 innerhalb des Messfensters liegende 5-Minuten-Renditen. Am Ende keine Zukunftsinformation.
3. Keine Duplikate, Lücken, fehlenden Schlusskurse, null/negative Kurse, zeitversetzten Märkte oder implizite Inner-Joins. Quelldateien, Zeitzone, Kopplung, Qualitätsbericht und SHA-256 registrieren, **bevor** die Korrelationszahlen berechnet werden.
4. Reproduktionsumgebung einschließlich Abweichungen von archivierter Python-/NumPy-/pandas-Version dokumentieren und vorhandenen Korrelationsrunner mit synthetischen Daten unter der lokalen Umgebung erneut verifizieren.
5. Die 7-Tage-Blockbootstrap-Intervalle nur als **deskriptive Unsicherheitsabschätzung** auffassen, nicht als unter allen Regimen kalibrierte Inferenz oder Beleg für Lead-Lag. Alle drei Korrelationen und drei Vorzeichenquoten vollständig berichten.

**Entscheidung A:** Methodisch **bedingt freigabefähig** für eine ausdrücklich *explorative/deskriptive* Messung an bereits verbrauchten Daten, sobald die obigen Datengates bestanden sind. Keine Erlaubnis zu automatischem Messstart aus diesem Dokument. Noch **keine** realen Korrelationszahlen erhoben. R5/R6-August–Oktober ist kein unverbrauchter Test.

## B: BTC→SOL-Richtung – **NO-GO FÜR ECHTE MARKTDATEN**
**Frage:** Zusätzlicher OOS-Log-Loss-Gewinn von BTC-Lags gegenüber SOL-Eigenhistorie, Ziel nächste abgeschlossene SOL-5-Minuten-Richtung.

**Positive Vorprüfung:** End-to-End-Synthetik bestanden. 600 synthetische Simulationen wurden auditiert: unabhängige Null 2/200 positive Gates, gemeinsame-Faktor-Null 1/200, fest eingebaute Alternative 200/200. Die Kontrollszenarien sind keine reale Marktvalidierung. 200 starke Alternativen simulieren **keine** Power für kleine Effekte; die exakten Binomialintervalle gelten nur für die geprüften Prozesse.

**Offene Gates:** Finales Originaldatenregister, unverbrauchter Zeitraum und Versiegelung 2027-04 bis 2027-06; validierter Realmarktdaten-Adapter und seine Zeitstempel; endgültige vorab fixierte Schätz- und Versionsbedingungen; statistische Gültigkeit außerhalb der zwei synthetischen Nullmodelle und geringe Effektgrößen; ausdrückliche spätere Einmal-Freigabe. Die R7-reservierte Periode 2027-01 bis 2027-03 bleibt für R8 gesperrt.

**Entscheidung B:** **Keine** Freigabe zur Prognosemessung mit echten BTC-/SOL-Daten. Keine Änderung an Trainings-, Testzeitraum, Parametern oder Modellauswahl aufgrund synthetischer Befunde.

## Trennlinie
A ist eine deskriptive Messung gleichzeitiger Bewegungen; B sucht zusätzliche Richtungsvorhersagbarkeit. Ein positiver Korrelationswert in A würde B **nicht** bestätigen. Beide Prozesse sind von produktiven TradingLab-/Freqtrade-Paper-Bots getrennt.

## Nächster Schritt
Ein einzelner **nur lesender lokaler Dateninventar- und Qualitätsvorcheck für A**, ohne Korrelationen zu berechnen. Der endgültige Messstart wird erst nach dessen Ergebnis mit eigenständiger, expliziter Freigabe entschieden.
