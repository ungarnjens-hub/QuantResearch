# R8 – Gebündeltes Phase-B-Audit (Vorbereitung)

**Stand:** 14.11.2026. **Status:** zur Ausführung vorbereitet, nicht ausgeführt; **keine Marktdatenfreigabe**. R7 und produktive Systeme bleiben unberührt.

## Ziel und Forschungsgrenzen

Die verschiedenen bereits versionierten synthetischen Prüfungen sollen in **einem isolierten Sammellauf** reproduziert werden. R8-A (Korrelation) und R8-B (BTC→SOL-Richtungsprognose) bleiben wissenschaftlich getrennte Teilstudien. Ein Bündeln von Rechenläufen begründet **keine** gemeinsame Signifikanz und darf die Vorregistrierung nicht verändern.

## Bestandteil des ersten Sammellaufs

1. **R8-A technische Datenintegrität**: UTC-5-Minuten-Raster, Close-Time-Semantik, Nullrenditen, fehlende und doppelte Kerzen, Positivität der Preise und reproduzierbare Gegenproben. Wiederverwendung der vorliegenden synthetischen Korrelationssuite.
2. **R8-A statistische Mechanik**: Pearson-Werte, drei vorab definierte Paare, Vorzeichenübereinstimmung und gepaarter Tagesblockbootstrap einschließlich gegenläufiger/unkorrelierter synthetischer Kontrollen.
3. **R8-B technische Datenintegrität**: Nur verfügbare historische Merkmale, Ziel in nächster 5-Minuten-Kerze, Sperrperiode Januar–März 2027, Nullziel-Maske, drei Monats-Refits und Fail-Closed-Prüfungen.
4. **R8-B statistische Mechanik**: Reproduktion des B1/M1-Log-Loss-Vergleichs und der bestehenden Tagesblockbootstrap-Berechnung auf einem **einzigen** synthetischen Testlauf.

Die bestehenden Skripte werden aus `~/QuantResearch-Git/studies/R8_synthetic/` **nur gelesen**, in ein neues isoliertes Verzeichnis kopiert und dort ausgeführt. Original-Skripte, JSON-Dateien, Market-Datasets, Git und TradingLab werden nicht verändert. Ein neuer Ergebnisordner entsteht bei jeder Ausführung, und Quelle/Ergebnis erhalten SHA-256-Prüfsummen.

## Zwei noch nicht enthaltene, verpflichtende Prüfungen

5. **Nullkalibrierung** (R8-B): Die tatsächliche komplette 5-Minuten-R8-B-Feature-/Refit-/Logit-/Score-Pipeline muss über mehrere voneinander unabhängige **synthetische** Volatilitätsregime und Nullwelten wiederholt werden. Nullwelten müssen *bedingten BTC-Zusatznutzen* ausschließen, nicht nur einen direkten kausalen BTC-Einfluss. Geeignete gemeinsame Faktorszenarien, verzögerte Effekte und seriell abhängige Schocks getrennt berichten.
6. **Power** (R8-B): Vorab begrenzte Varianten mit schwachem, künstlich eingebautem Zusatznutzen; Erkennungswahrscheinlichkeit, realisierte Effektgröße und Unsicherheitsintervall über Simulationsläufe berichten. Kein Nachjustieren auf gewünschte Erfolgsquote.

Für 5 und 6 fehlen derzeit ein **vorab auditiertes vollständiges Simulationsmodell**, exakte Replikationszahlen und eine Rechenzeit-/Leistungsprüfung auf dem vorhandenen PC. Sie dürfen weder durch die bisher durchgeführten vereinfachten R7-Simulationen noch durch einen einzelnen R8-B-Synthetiklauf ersetzt werden. Deshalb wird im Sammelresultat ausdrücklich `NOT_RUN` erfasst. **Kein Phase-C-Go möglich.**

## Prüfreihenfolge und Entscheidung

- Vor Lauf: Vorhandene Dateien und Abhängigkeiten lesend prüfen; SHA-256 sichern.
- Im Lauf: Die vier vorhandenen technischen/methodischen Prüfpakete ohne Eingriff in die Versionen isoliert reproduzieren. Jeder Test bleibt einzeln PASS/FAIL.
- Danach: Null- und Power-Simulation getrennt entwerfen und fachlich prüfen, **erst dann** in denselben Batch integrieren.
- FAIL: Quelle fehlt, unerwartetes Ergebnisformat, Prüftest scheitert oder Zeit-/Ressourcenlimit wird erreicht. Keine stillen Reparaturen.
- PASS der vier Suiten bedeutet nur: *bisherige synthetische Grundprüfungen reproduziert*, **nicht** „signifikanzgeprüft“ oder „Markttest freigegeben“.

## Bedienung nach GitHub-Archivierung

```bash
python ~/QuantResearch-Git/studies/R8_synthetic/R8_phase_b_sammelaudit.py --preflight
python ~/QuantResearch-Git/studies/R8_synthetic/R8_phase_b_sammelaudit.py --run --output-root ~/QuantResearch/R8_Batch
```

**Forschungsstatus:** Phase B, keine echten Marktdaten, keine Strategie/Orders, kein Zugriff auf Paper-Bots.
