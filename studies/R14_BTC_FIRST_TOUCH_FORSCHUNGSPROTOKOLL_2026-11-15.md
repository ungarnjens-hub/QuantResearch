# R14 – BTC First-Touch und Einstiegspfad, registriertes Explorationsprotokoll

Datum: 2026-11-15. Status: A/B-Plan und synthetische Vorprüfung, **keine reale BTC-Messung in dieser Umgebung**.

## Ziel und falsifizierbare Hypothese

Der Nutzer möchte für die drei unveränderten R12-Einstiegsklassen (Pullback, Breakout, Mean Reversion) wissen, wie oft BTC nach einer Entry-Entscheidung **zuerst** eine definierte Gewinnbewegung, **zuerst** eine Verlustbewegung oder keines von beiden innerhalb einer Stunde erreicht. Ein anschließendes positives Nettoergebnis wird **nicht** vorausgesetzt. Testhypothese: Bei mindestens einer Klasse ist die mittlere konservativ simulierte, kostenbereinigte First-Touch-Rendite positiv. Nullhypothese: keine Klasse zeigt das im festgelegten diagnostischen Versuch.

## Datenbasis und Identität

R12-Festcode `R12_3_Strategien_BTC_Explorativ.py` unverändert aus `~/QuantResearch-Git/studies/`, SHA256 `7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d`; Daten-BTC-Parquet `~/Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m/`, September 2024 bis Dezember 2025, Originalhashes aus `R13_RESULTS.json` werden verifiziert. 45.279 ursprüngliche R13-Signale aus `~/QuantResearch/R13_BTC_EntryPaths/Sep2024_Dec2025_v1/R13_ENTRY_PATHS.csv`. Unveränderter R12-Entry, R13-Signal am abgeschlossenen j, Einstieg Open j+1. Keine Zugriffe schreibend auf Originaldaten, Profile oder Paper-Bots. Keinerlei Börsenaufträge.

## Eine feste diagnostische Ausführungsregel (keine Parameteroptimierung)

- Stop-Grenze: -14 Basispunkte vom Open-Einstieg, Kursziel: +28 Basispunkte vom Open-Einstieg. Das ist ein illustrativer 1:2-Distanzvergleich, **nicht** eine bereits gefundene optimale ATR-Stoppregel.
- Erster Kontakt über OHLC der 12 folgenden vollständigen 5m-Bars. Stop und Ziel innerhalb desselben Bars => konservativ Stop zuerst. Erreicht die Eröffnung eines Bars bereits eine Barriere, Exit zu diesem Open-Preis. Kein Trigger => Zeitexit Open nach 60 Minuten.
- Simulierter durchschnittlicher Nettoertrag: realisierte Richtungsrendite minus 14bp feste Modellkosten. Stress-Variante minus 24bp. Die Kosten sind vereinfachte Annahmen, **keine** tatsächlichen historischen Funding-Abrechnungen.
- Die Signale sind **überlappende Ereignisbeobachtungen**, nicht gleichzeitig ausführbare Portfolio-Trades. Gewinnquote/Profit-Faktor hier dürfen **nicht** als Portfolio-Backtest oder Live-Profitabilität beworben werden.
- R13 MFE/MAE muss für jedes Signal im 60m-Horizont zu den Originalkerzen passen. Der Zeitpunkt des höchsten günstigen Bars wird nur deskriptiv ausgewiesen. Ein Peak nach Stop ist **kein** handelbarer TP.

## Marktumfeld

Beschreibende Gruppen nur mit beim Einstieg bekanntem Vorlauf: Signaltrend passend vs. gegenläufig zur 60m-Richtung, jeweils 2024 und 2025, pro Strategie. Keine nachträgliche Auswahl einer profitablen Untergruppe als „bestätigter“ Filter. Anzahl, First-Touch-Raten, Konfliktrate, mittlerer Brutto- und Modell-Nettoertrag, PF, Zeit bis Exit sowie günstige Bewegung vor einer Stop-Ausführung. Die Ergebnisse werden vollständig berichtet, auch bei Verlusten.

## Stop-Regel und Risiken

OHLC-Bars liefern nicht immer die zeitliche Tick-Reihenfolge. Die Stop-First-Annahme schützt vor optimistischer Intrabar-Auswertung, kann aber echte Ausführungswege nicht exakt rekonstruieren. Spread, Slippage, Markttiefe, Requotes und tatsächliche Funding-Zahlungen sind noch nicht validiert. Historische Daten 2024/2025 wurden bereits mehrfach untersucht; **kein unabhängiger Holdout, keine kalibrierte Signifikanz oder Multiplikitätskontrolle**. Eine spätere profitorientierte Regel erfordert ein neues, vorher eingefrorenes Forschungsdesign, chronologische Validierung und anschließend realitätsnahe Paper-Ausführung mit Freqtrade 2026.9.

## Entscheidungsregel

Ist für jede Strategie der mittlere modellierte Nettoertrag negativ oder sehr unsicher, wird **keine** Strategie freigegeben. Positive explorative Gruppen werden ausschließlich als neue Hypothesen archiviert, nicht nachträglich als getesteter Champion ausgegeben. Eine spätere Verbesserung von Stop/TP oder Signalfrequenz ist ein neues Experiment und muss zuerst die für den Eintrittszeitpunkt bekannten Merkmale kausal erklären.

## Fachgrundlage

Triple-Barrier-Labeling: Marcos López de Prado (2018), *Advances in Financial Machine Learning*, Kapitel 3.4: erster Kontakt zu Gewinn-, Verlust- oder Zeitbarriere. Bailey et al. (2017), *The Probability of Backtest Overfitting*, Journal of Computational Finance, DOI 10.21314/JCF.2016.322: Selektions- und Mehrfachtestproblematik.
