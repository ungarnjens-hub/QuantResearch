# R8: Kombinierter v2-Nachaudit, Phase B

**Stand:** 14. November 2026. **Ergebnis: Technische Prüfungen bestanden, Hauptlauf weiterhin NO-GO.**

## Prüfungsumfang

1. Quellcodevergleich gegen unveränderte archivierte v1.
2. Manipulationstests: fehlende, falsche und ausdrücklich negative Freigabe; injizierter Simulationsfehler.
3. Ein einziger vollständiger synthetischer Prognoselauf als Ressourcenprobe.

**Keine Marktdaten; keine produktiven Dateien; keine 600er-Kalibrierung.**

## Codeidentität

- Ursprünglicher Kalibrierungscode SHA-256: `f2cd2d3700a23b14b2fc5b424347c0fbebfc116101d078895d58ae3075fd4975`
- v2 SHA-256: `c67ded5c5d2812d20608ad9508ad6c6dc4d3efbee9708dbaa09dfa5ab67fe6f9`
- Eingefrorene R8-Prognosepipeline SHA-256: `6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff`
- Registriertes Prüfprotokoll SHA-256: `b3284c6e92e1de529b300b51556990e6b2d8076f06c2685fead783a6bde49bff`

Der Vergleich ergibt: `prices`, `load_frozen`, `simulate` und `clopper_pearson` sowie Seed-, Szenarien-, Refit- und Zeitraumkonstanten sind unverändert. v2 ergänzt Zugriffsprüfung, Selbsttests, Fehlerarchivierung und die neue Ablaufsteuerung. **Der Audit belegt keine vollständige wissenschaftliche Eignung des Datenprozesses.**

## Fehler- und Freigabetests

| Prüfung | Ergebnis |
|---|---|
| `--run` ohne Freigabedatei | PASS, vor Modellstart abgelehnt |
| Freigabedatei fehlt | PASS, abgelehnt |
| `approved=false` | PASS, abgelehnt |
| Falscher Scope | PASS, abgelehnt |
| Falscher Runnerhash | PASS, abgelehnt |
| Injizierte Ausnahme in Replikation | PASS, `FAILURE.json` geschrieben |
| Szenario, Seed, Traceback, Hash in Fehlerdatei | PASS |
| Keine Erfolgssummary nach Abbruch | PASS |

Die Tests zeigen die Schutzwirkung im **geprüften Fehlerbereich**. Eine Ausnahme vor oder nach der Replikationsschleife wird nicht zwingend mit Seed archiviert. Ein Hardware-/Stromausfall wird nicht abgedeckt.

## Ressourcenprobe

Ein vollständiger synthetischer `independent_null`-Durchlauf mit Seed `20261114000`:

- **26.204** erzeugte 5m-Prognosen, davon **25.934** auswertbar und **270** Nullrenditen.
- **0,887 Sekunden** für eine Replikation in dieser Testumgebung.
- **276.064 KiB** maximaler Prozess-RSS (ca. 270 MiB), inklusive Python-Interpreter/Bibliotheken.
- Prognosevergleich: kein positiver Befund; **dies ist nur ein einzelner technischer Smoke-Test, keine Signifikanzkalibrierung**.

**Umgebung der Probe:** Python 3.13.5, numpy 2.3.5, pandas 2.2.3, scipy 1.17.0, sklearn 1.8.0. Der Nutzer verwendet laut eigener Konsole Python 3.14 / scikit-learn 1.9.1. Laufzeit und Speicher sind nicht auf seinen Rechner übertragbar.

Eine `FutureWarning` für `LogisticRegression(penalty=None)` wurde beobachtet. Die heute verwendete API funktioniert im Test, aber die spätere Entfernung des Parameters muss bei einer neuen Bibliotheksversion erneut auditiert werden; eingefrorenen Modellcode nicht stillschweigend ändern.

## Freigabeentscheidung

**Technisches Teil-Audit: PASS, mit Einschränkungen.**

**600 unabhängige Replikationen: NO-GO.** Kein separates genehmigtes Manifest angelegt. Vorab die unabhängige methodische Prüfung, die vollständige Null-/Alternativdefinition sowie den lokalen Leistungscheck mit der beim Nutzer tatsächlich installierten Bibliotheksversion dokumentieren.

**R8 Phase C mit echten Marktdaten: NO-GO.** R5/R6/R7 und TradingLab bleiben unverändert.
