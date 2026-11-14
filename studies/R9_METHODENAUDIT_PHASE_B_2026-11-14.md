# R9 – Methodenaudit Phase B (Version 1.0)
**Datum:** 14.11.2026  
**Basis:** `R9_INTRADAY_MOMENTUM_PHASE_A_2026-11-14.md`, Commit `7bfbd53`  
**Ergebnis:** **B: NO-GO für Phase C bis zur Korrektur und Freigabe.** Keine Marktdatenmessung, kein Backtest, keine Handelsstrategie.

## 1. Gegenstand
Die registrierte Hauptfrage lautet: Ist die vorzeichenbereinigte zukünftige 30-Minuten-Logrendite bei starken abgeschlossenen 30-Minuten-Impulsen mit hohem Volumen (`v>=1.5`) höher als bei starken Impulsen ohne hohes Volumen (`v<1.5`)? Drei Märkte werden **getrennt** geprüft: BTC, ETH und SOL, Binance USD-M Perpetual, Last-Trade-OHLCV, 5m.

**Wichtig:** Die Studie untersucht zunächst eine *Renditeasymmetrie im Markt*, noch keine nach Kosten profitable Handelsstrategie.

## 2. Literaturprüfung
- Shen, Urquhart & Wang, *Bitcoin intraday time series momentum*, Financial Review 57 (2022), DOI `10.1111/fire.12290`: erstes volumenbezogenes Halb-Stunden-Fenster eines Intraday-Ansatzes; kein Beleg für die konkrete 5m-z-Score-Schwelle. Abstract nennt Liquiditätsbereitstellung als mögliche Erklärung; der im Phase-A-Dokument beschriebene alleinige Mechanismus „verzögerte Informationsverarbeitung“ ist zu eng.
- Wen, Bouri, Xu & Zhao, *Intraday return predictability in the cryptocurrency markets: Momentum, reversal, or both*, NAJEF 62 (2022), DOI `10.1016/j.najef.2022.101733`: beide Richtungen kommen vor und hängen von Marktbedingungen ab.
**Bewertung:** Fachlicher Ausgangspunkt plausibel, spezifische Konfiguration bleibt ungeprüfte Forschungskonvention.

## 3. Technische und statistische Auditpunkte
| ID | Audit | Status / erforderliche Entscheidung |
|---|---|---|
| B01 | Datenprovenienz und Verbrauchsregister | **OFFEN**: BTC/ETH/SOL 5m Rohdateien und Hashes registerpflichtig. Aug–Okt 2026 aus R5/R6/R8 bereits verbraucht. Jan–Mär 2027 für R7 und Apr–Jun 2027 für R8-B reserviert; keine stille Doppelbelegung. |
| B02 | Ereignis-Zeitstempel | **BEDINGT KORREKT**: Open-Time einer Kerze plus 5m = Schlusszeit. Ereignis nach Abschluss der sechsten Impulskerze; keine Daten mit Schlusszeit >t. |
| B03 | 288 vorherige Renditen | **PRÄZISIEREN**: 288 5m-Logrenditen vollständig vor Beginn des 30m-Impulsfensters, dafür 289 historische Schlusskurse erforderlich. Keine Impulskerze darf in die Volatilitätsreferenz rutschen. |
| B04 | Volumenbaseline | **PRÄZISIEREN**: 288 historische Volumenkerzen vollständig vor Beginn der Impulsperiode; Basiscurrency/Binance-Einheiten verifizieren. Bei Median <=0 Ereignis als ungültig protokollieren. |
| B05 | 30m-Label und Ausführbarkeit | **KORREKT ALS PROXY**: `sign(r30(t))*log(C(t+30m)/C(t))`. Die Erkennung ist frühestens nach dem Schluss C(t) möglich; dieser Schlusskurs darf **nicht** später als garantierter Entry-Preis ausgegeben werden. |
| B06 | Einmalige Event-Auswahl | **AUSWIRKUNG DOKUMENTIEREN**: gemeinsame deterministische Sperre für t+5 bis t+30 für beide Gruppen; dadurch werden Gruppenhäufigkeiten beeinflusst, keine nachträgliche Retuningsuche. |
| B07 | Vergleichbarkeit der Gruppen | **METHODISCH KRITISCH**: M1/B1 können sich systematisch nach Impulsstärke, UTC-Zeit und Volatilitätsregime unterscheiden. Primäres Delta misst eine *unadjustierte Assoziation*, keinen isolierten kausalen „Volumeneffekt“. |
| B08 | Bootstrap | **NOCH NICHT FREIGEGEBEN**: Replikate sollen 7 zusammenhängende UTC-Kalendertage gemeinsam für M1/B1 ziehen; keine Rendite- oder Einzelereignis-IID-Bootstraps. Grenztags- und Leere-Gruppe-Verhalten vorab synthetisch prüfen. |
| B09 | Inferenz/Mehrfachtests | **NOCH NICHT FREIGEGEBEN**: 95%-Perzentil-CI und einseitige H1 rechtfertigen ohne kalibrierten Test keine unkontrollierte Signifikanz-/Holm-Aussage. Drei Märkte als Testfamilie behandeln. |
| B10 | Stichprobenpräzision | **OFFEN**: vor Marktmessung Mindest-Ereigniszahl je Gruppe/Asset und gewünschte Mindestpräzision festlegen; bei zu geringer Zahl „ungeklärt“, nicht „negativ“. |
| B11 | Holdout | **BLOCKIERT**: Entwicklungs- und echte unbenutzte Testzeitfenster samt Embargo/Überlappung dokumentieren, ohne künftige Testwerte einzusehen. |
| B12 | Archivierung | **OFFEN**: exakte Programmversion, Input-Hashes, ausgeschlossene Ereignisse, Kalendertage, Stichprobengrößen, Bootstrap-Seed, Log und Ergebnis vorsehen. |

## 4. Methodische Präzisierung vor jeder Messung
1. **Zuerst Datenaudit ohne Y-Berechnung:** Existenz, Vollständigkeit, OHLCV/UTC, Volumeneinheiten, erstes/letztes Datum, historische Datensatznutzung, Hashes. Produktive TradingLab-Dateien nicht anfassen.
2. **Synthetischer Prüfdatensatz vorab:** (a) Nullrelation zwischen Gruppen, (b) positives bekanntes Delta, (c) deterministische Ereignis-Sperre, (d) 5m-Zeitgrenzen, (e) 7d-Bootstrap mit leeren Gruppen, (f) Ausbleiben jeder Look-ahead-Nutzung. Synthetische Befunde niemals als reale Marktleistung darstellen.
3. **Kein fremdes Testfenster umwidmen:** Für historische bereits konsumierte Daten ist ausschließlich eine klar gekennzeichnete *explorative* Messung zulässig. Ein noch nicht existierender beziehungsweise nicht vollständig abgeschlossener Zeitraum kann kein vorliegender Blindtest sein.
4. **Konfirmatorische Kriterien:** Effektgröße samt KI, drei Märkte und Testfamilie, minimale Gruppengrößen, zulässige Nulltest-/Mehrfachtest-Methode, Stabilitätskriterien und minimale wirtschaftlich relevante Renditegröße schriftlich fixieren; eine Marke darf individuell bestehen, aber keine nachträgliche Marktauswahl.
5. **Ökonomischer Anschluss:** Erst nach belastbarem Mechanismusnachweis separate **Phase-A-Neuregistrierung** für ausführbare Ein- und Ausstiege und Netto-PnL: Ausführung ab dem frühesten tatsächlich verfügbaren Quote-/Kerzenzeitpunkt, realistische Futures-Gebühren, bid/ask-Spread, Slippage, Funding, Stop-/Gap-Risiko, Liquidität; ausschließlich unberührte Daten zur finalen Renditebeurteilung. Keine produktiven Änderungen.

## 5. Freigabestatus
- **Phase A:** protokolliert, Git-Commit `7bfbd53`.
- **Phase B:** methodisch geprüft; B01/B08/B09/B10/B11 offen. Protokoll nicht rückwirkend umdeuten, Korrekturen als versionierter Nachtrag **vor Ergebnismessung**.
- **Phase C:** **NICHT FREIGEGEBEN**.
- **Nächste sachliche Arbeit:** ein einziger isolierter, rein lesender Bestands- und Verwendungscheck; anschließend ein gebündelter synthetischer E2E-Methodentest. Kein wahlloser Backtest.

## 6. Quellen
- https://doi.org/10.1111/fire.12290
- https://doi.org/10.1016/j.najef.2022.101733
