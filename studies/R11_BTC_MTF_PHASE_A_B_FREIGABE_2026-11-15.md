# R11: BTC Multi-Timeframe-Rücksetzer | Version 1.0

**Datum:** 15. November 2026  
**Arbeitsphasen:** A: neues Forschungsdesign, B: technischer Methodenaudit, C: **einmalige explorative** Messfreigabe nach erfolgreichem Preflight und erfolgreicher Archivierung. Keine Freigabe für konfirmatorische Aussagen, Strategiebetrieb oder Orders.

## Forschungsziel und Fachbasis

**Frage:** Liefert die letzte *vollständig abgeschlossene* BTC-Stundenkerze zusätzliche Informationen über die Richtung der nächsten 15 Minuten nach einem kurzfristigen 5-Minuten-Rücksetzer? Liefern zusätzliche abgeschlossene 15- und 30-Minuten-Kerzen inkrementell noch mehr Informationen?

Die Hypothese folgt dem bekannten Spannungsfeld zwischen Trendfortsetzung und Gegenbewegung auf unterschiedlichen Horizonten. Fachliche Anker: Zaremba et al. (2021), DOI `10.1016/j.irfa.2021.101908`; akademische Forschung zu purged/embargoed Zeitreihenvalidierung, López de Prado (2018), *Advances in Financial Machine Learning*, Kap. 7. Diese Quellen garantieren keinen BTC-5m-/60m-Vorteil.

**H1a (primär, explorativ):** Das festgelegte Modell B mit 5m- und 60m-Merkmal hat auf 2025 einen niedrigeren Brier Score als das Modell A mit ausschließlich 5m-Merkmal. **H1b (sekundär):** Modell C (5m/15m/30m/60m) verbessert den Brier Score zusätzlich gegenüber Modell B. Beides wird nur deskriptiv geprüft: keine p-Werte, keine konfirmatorische Behauptung.

## Registrierte Daten und Verwendungsstatus

- Nur **BTCUSDT linear perpetual, Binance USD-M Futures, last-trade-Kerzen**, 5m.
- Originaldaten lesend: `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m/`, 16 Monats-Parquetdateien September 2024 bis einschließlich Dezember 2025, 140.256 5m-Kerzen, UTC.
- September–Dezember 2024: **Modelltraining** und rein explorative Beschreibung der Marktbedingungen.
- Januar–Dezember 2025: **spätere chronologische explorative Auswertung**. Dieser Zeitraum wurde in anderen Forschungsprojekten bereits betrachtet und ist **kein unberührter Blindtest**.
- Keine Nutzung der R7/R8-reservierten Zukunftsdaten. Originale und produktive Profile/Bots bleiben unverändert.
- Der Runner prüft vor Messbeginn Datenherkunft, 5m-Vollständigkeit, abgeschlossene Kerzen, OHLCV, Zeitstempel, UTC und SHA-256 der 16 Originaldateien. Input-Hashes werden im Ergebnis gespeichert.

## Vorab fixierte Ereignisse und Features

- Entscheidung bei Abschluss einer 5-Minuten-Kerze (`open_time + 5min`). Keine nachträgliche Änderung der Parameter anhand der Ergebnisse.
- Ereignis: **negativer 5m-Logreturn < −0,5 × Standardabweichung der 288 vorherigen 5m-Renditen**. Die aktuell betrachtete 5m-Kerze darf nicht in die 288 historischen Renditen hineinrutschen. Kein Mindestvolumen, keine Uhrzeitsuche.
- Baseline A: standardisierter letzter 5m-Logreturn.
- Erweiterung B: A + standardisierter **letzter abgeschlossener 60m-Logreturn**.
- Erweiterung C: B + standardisierte **letzte abgeschlossene 15m- und 30m-Logreturns**.
- Gröbere Timeframes werden aus 5m-Kerzen **UTC-uhrzeitlich verankert** und als tatsächlich abgeschlossene 15m/30m/60m-Kerzen verwendet. Bei 10:05 darf etwa kein späterer 11:00-Stundenabschluss benutzt werden. Es wird ausdrücklich **kein** unabhängiger Dateninhalt der verschiedenen Timeframes behauptet; 15/30/60 können sich überschneiden.
- Primäres Label: BTC-15m-Schlusskursrichtung in den nächsten drei vollständigen 5m-Kerzen. Nullrenditen werden für den binären Modellscore ausgeschlossen und gezählt. Primärer Vergleich: gepaarte **Brier-Score-Verbesserung** `Brier(A)-Brier(B)` auf exakt denselben 2025-Zeitpunkten. Sekundär `Brier(B)-Brier(C)`. Negative Verbesserung = Zusatzmerkmale verschlechtern Prognosen.
- Deskriptiv: 15m- und 30m-Folgerendite in Basispunkten und Aufwärtsanteile nach letzter positiver versus negativer **abgeschlossener** 60m-Kerze. Die 30m-Rendite ist keine weitere optimierte Zielgröße.
- Alle Ereignisse mit Zukunftslabel nach Ablauf des jeweiligen Jahres werden ausgeschlossen. 2025 dürfen 2024-Kerzen ausschließlich für tatsächlich historisch verfügbare Feature-Warm-ups nutzen; Labels aus 2025 gelangen niemals ins Training.

## Statistische Methode, Grenzen und wirtschaftlicher Bezug

- Drei **festgelegte** logistische Modelle, StandardScaler ausschließlich auf 2024-Trainingsdaten angepasst, Logit L2 `C=1.0`, `lbfgs`, `max_iter=600`, Seed `20261115`, keine Suche von Hyperparametern, keine Anpassung nach Ansicht von 2025.
- Baseline: konstante 2024-Trainingsquote. Statistik: Brier und Log-Loss für alle Modelle, primär Brier-Verbesserung. 5.000 gepaarte zirkuläre Moving-Block-Ziehungen über sieben zusammenhängende **UTC-Tage** aus 2025, Seed 20261115. Die resultierenden 95%-Perzentilintervalle sind **rein deskriptiv**. Überlappende 15m-Labels, Regimewechsel und die aus R9 bekannte unzureichende Nullkalibrierung verhindern jede Signifikanzbehauptung.
- Keine Gleichsetzung von Richtungsvorhersage, durchschnittlichen Kursbewegungen, mechanischer Handelsregel oder **Netto-Profitabilität**. Historische Schlusskurse sind keine garantiert ausführbaren Einstiegspreise. Keine Gebühren-, Spread-, Slippage-, Funding-, Stop- oder Portfolio-Modellierung; diese wären erst Inhalt eines gesonderten vorregistrierten Wirtschaftsdesigns bei begründetem Potenzial.
- Etwaige Befunde gelten nur als **explorative Kandidaten** und müssen bei einer nachfolgenden konfirmatorischen Prüfung mit unangetasteten Daten validiert werden.

## Gebündelter Audit und Freigabe-Gates

1. Originaldaten und Schema read-only prüfen, 16 Dateihashes registrieren, Fehlstellen und Schlusszeitstempel fail-closed.
2. Synthetischer E2E-Check: 288-Historie vor letztem 5m-Return; kein Look-ahead; 15/30/60m nur bei geschlossenem UTC-Kerzenende; Zukunftspreismanipulation verändert alte Merkmale nicht; 2024/2025-Partitionen und Zielhorizont getrennt; gepaarter Tages-Blockbootstrap reproduziert bekanntes Delta.
3. Die **unveränderte** Datei `R11_BTC_MTF_einmaliger_forschungslauf.py` samt diesem Dokument vor Ausführung in Git `main` committen und pushen. `--preflight` vor `--run` im **selben Konsolenblock**. Bei FAIL kein Messlauf.
4. Ausgabe ausschließlich unter `~/QuantResearch/R11_BTC_MTF/2024_train_2025_exploratory_v1/`, exklusiv neu; vorhandener Ordner => STOP statt Überschreiben.
5. Beide Ergebnisse (auch negative), Rohhashes, Quellhash und Einschränkungen als JSON/Markdown dokumentieren. Keine produktiven Handelsdateien ändern.

## Freigabestatus

**Eine einmalige, nur explorative Phase-C-Ausführung ist nach dokumentiertem Preflight erlaubt.** Diese Erlaubnis erstreckt sich weder auf eine Strategieentwicklung oder Handelssimulation noch auf eine eigenständige konfirmatorische Datenprüfung. Bei technischen Fehlern: stoppen und versioniert korrigieren, keine stillschweigende Ergebnisoptimierung.
