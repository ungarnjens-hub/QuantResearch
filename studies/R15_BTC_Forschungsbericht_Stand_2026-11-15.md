# BTC-Preiszonen und Einstiegserkennung: Forschungsbericht R12–R15

**Stand: 15. November 2026**  
**Gegenstand:** Binance BTC/USDT lineare Perpetual-Futures, historische 5m-Last-Trade-OHLC.  
**Messstatus:** R12–R14 anhand der tatsächlich hochgeladenen CSV-/JSON-Dateien ausgewertet; R15-Zonenmodell ist **vorbereitet und synthetisch getestet, aber mangels Original-Parquetdaten in dieser Arbeitsumgebung noch NICHT am realen BTC-Markt gemessen**.  
**Status der Erkenntnisse:** Explorativ, keine unabhängig bestätigte oder live nutzbare Strategie.  

## 1. Fragestellung und wichtigste Antwort

Gesucht wird **nicht** die größte nachträglich sichtbare Bitcoin-Bewegung, sondern eine bereits bei der Entscheidung bekannte Situation, in der ein **nach der Bestätigung tatsächlich handelbarer Einstieg** eine realistische Gewinnbewegung **vor** einer schädlichen Gegenbewegung erreicht und nach Kosten einen positiven Erwartungswert hat.

Die vorhandenen echten Messungen beantworten bereits einen Teil:

- Die bisherigen **Trend-Pullback-, Breakout- und Mean-Reversion-Signale aus R12** sind sehr häufig und unter den diagnostischen Regeln wirtschaftlich ungeeignet.
- Insbesondere **Mean Reversion** erkennt oft eine starke Bewegung, aber nicht zuverlässig deren Ende. 2025 werden 62,9 % der ausgestoppten Mean-Reversion-Signale schon innerhalb der ersten Einstiegskerze getroffen (5m-OHLC kann die genaue Sekunde nicht zeigen).
- MFE-Peaks sind oft groß, aber vielfach **nach** dem Stop; sie sind kein realisierbarer Tradegewinn. Ein früher Eintritt im fallenden Markt ist deshalb ökonomisch nicht gleichwertig mit einem bestätigten Eintritt nach einer Stabilisierung.
- Der untersuchte **60m-Trendindikator alleine** trennt erfolgreiche und gescheiterte Einstiege bisher nicht zuverlässig. Für eine belastbare Untersuchung von **historischen Preiszonen** fehlen in den hochgeladenen Ereignisdateien die früheren 3-, 14- und 21-Tage-OHLC-Daten.
- Die wissenschaftlich plausiblere neue Hypothese lautet: **vorher bekannte Zone + Berührung + zeitlich nachfolgende bestätigte Reaktion + strukturbezogener Stop** kann wirtschaftlich besser sein als sofortiger Eintritt bei der Berührung. Das ist R15, noch kein Marktergebnis.

## 2. Tatsächlich vorhandene Quellen und Abgleich

Verwendete hochgeladene Quellen:

| Quelle | Geprüfter Inhalt | Rolle |
|---|---|---|
| `R12_TRADES.csv`, `R12_RESULTS.json` | 20.738 ausgeführte R12-Simulationen | Referenz der bisherigen Ausstiegslogik |
| `R13_ENTRY_PATHS.csv`, `R13_RESULTS.json` | 45.279 unabhängig gezählte Einstiegssignale; MFE/MAE nach 15/30/60/120 min | Beobachtete Kursmöglichkeiten |
| `R14_FIRST_TOUCH_EVENTS.csv`, `R14_REPORT.md` | 45.279 dieselben Ereignisse, First Touch, Ausstiegsgrund und 60m-Peak-Kerze | Stop-vor-Ziel, Timing und tatsächliche Erreichbarkeit |

Die beiden Ereignistabellen wurden anhand der Schlüssel `(period, strategy, signal_idx)` vollständig 1:1 verbunden: **45.279 Zeilen, keine fehlenden Zuordnungen und keine doppelten Schlüssel.** Die First-Touch-Datei hat keine leeren Pflichtwerte in den geprüften Spalten.

R14 trennt September–Dezember 2024 und Januar–Dezember 2025. Original-Preisparquets liegen in dieser Arbeitsumgebung **nicht** vor. Es wäre methodisch falsch, daraus ein angeblich bereits gemessenes R15-Zonenresultat zu erfinden.

## 3. Gesamtergebnisse: First-Touch statt MFE-Fantasiegewinnen

**Diagnoseannahmen R14:** Stop 14 bp (0,14 %), Take-Profit 28 bp (0,28 %), höchstens 60 Minuten, nächster Open als Einstieg, konservativer Stop zuerst bei einer Stop/TP-Kollision innerhalb derselben Kerze, pauschale Roundtrip-Kosten 14 bp. Alle Ereignisse unabhängig ohne reale Portfolio-Positionsbegrenzung; teilweise zeitlich überlappende Gelegenheiten.

| Strategie | Jahr | Signale | Gewinnziel zuerst | Stop zuerst | Zeitablauf | mittleres Nettoergebnis / Signal |
|---|---|---:|---:|---:|---:|---:|
| Pullback | 2024 | 4.405 | 29,26 % | 64,86 % | 5,88 % | −14,61 bp |
| Pullback | 2025 | 11.621 | 28,67 % | 61,75 % | 9,58 % | −14,03 bp |
| Breakout | 2024 | 5.329 | 26,67 % | 65,62 % | 7,71 % | −15,38 bp |
| Breakout | 2025 | 16.024 | 24,85 % | 60,59 % | 14,56 % | −14,84 bp |
| Mean Reversion | 2024 | 2.043 | 31,28 % | 66,57 % | 2,15 % | −14,44 bp |
| Mean Reversion | 2025 | 5.857 | 29,86 % | 64,83 % | 5,31 % | −14,38 bp |

Alle drei wurden 2024 und 2025 **durchweg negativ**. Mehr Trades oder ein leicht besserer Targetanteil erklären keine Wirtschaftlichkeit. Ohne Zeit-Exits und Kurssprünge gilt bei 28bp Ziel, 14bp Stop, 14bp Kosten:

- Gewinn nach Kosten bei Ziel: **+14 bp**.
- Verlust nach Kosten bei Stop: **−28 bp**.
- Erforderliche Zielquote im reinen Zwei-Ausgangs-Modell: **mehr als 66,7 %**. Die beobachteten 25–31 % liegen weit davon entfernt. Für echte Fälle mit Zeit-Exit, Preis-Gaps, variablen Risikobeträgen ist die vollständige Ausführungssimulation maßgeblich.

## 4. Wo verlieren unsere Einstiege? Die frühe Gegenbewegung

Die folgende Auswertung verwendet die aus R14 **tatsächlich ausgestoppten** Signale als Nenner:

| Strategie | Jahr | Ausgestoppte Signale | davon Stop bereits in der Einstiegskerze | vor Stop kein nachweisbarer +14bp günstiger Ausschlag |
|---|---|---:|---:|---:|
| Pullback | 2024 | 2.857 | 38,6 % | 80,5 % |
| Pullback | 2025 | 7.176 | 37,1 % | 82,5 % |
| Breakout | 2024 | 3.497 | 45,1 % | 84,6 % |
| Breakout | 2025 | 9.709 | 37,4 % | 84,9 % |
| Mean Reversion | 2024 | 1.360 | 71,4 % | 85,2 % |
| Mean Reversion | 2025 | 3.797 | **62,9 %** | **82,9 %** |

**Interpretation:** Die bisherige Mean-Reversion-Erkennung verwechselt offenbar häufig „stark gefallen“ mit „Boden erkennbar“. Eine spätere Umkehr ist möglich, aber **der sofortige Einstieg hat sie nicht ausreichend vorweggenommen**. Dass viele Stop-Exits keine nachweisbare +14bp-Bewegung vor dem Ausstieg erzielten, stützt eine Untersuchung der Einstiegsqualität. Es belegt noch **nicht**, welche Bestätigung die Lage verbessert.

**Grenze:** `max_favorable_before_exit_bp` wertet nur vor der Ausstiegskerze eindeutig erfasste Ausschläge. Bei Stop/Ziel in derselben 5m-Kerze ist die Intrabar-Reihenfolge ungeklärt und wird konservativ gegen den Trade entschieden. Die wahre Mikrostruktur benötigt Tick-/Trade- oder Orderbuchdaten.

## 5. Wie groß sind die Kurs-Peaks tatsächlich?

Die **MFE über die vollen 60 Minuten** kann erst nach dem Stop entstehen und ist kein realisierter Take-Profit.

| Einstieg | Jahr | Median günstige MFE | Schwelle oberes Viertel | Median ungünstige MAE |
|---|---|---:|---:|---:|
| Pullback | 2024 | 26,5 bp | 51,0 bp | 27,9 bp |
| Pullback | 2025 | 24,6 bp | 47,6 bp | 24,8 bp |
| Breakout | 2024 | 25,3 bp | 51,0 bp | 28,1 bp |
| Breakout | 2025 | 20,4 bp | 42,4 bp | 22,5 bp |
| Mean Reversion | 2024 | **41,4 bp** | **74,6 bp** | 37,5 bp |
| Mean Reversion | 2025 | **32,8 bp** | **62,9 bp** | 33,7 bp |

Bei der Hälfte der Mean-Reversion-Ereignisse lag 2025 die günstigste Bewegung innerhalb einer Stunde bei mindestens 0,328 %. Gleichzeitig lag die Median-Gegenbewegung bei 0,337 %. **Diese beiden getrennt über alle Signale berechneten Mediane liefern keine Reihenfolge!** Sie können nicht als auszahlbares CRV interpretiert werden.

### 5.1 Der „späte Peak“ bei bereits ausgestoppten Signalen

Von den ausgestoppten Signalen erreichten in den restlichen vollen 60 Minuten **nach oder inklusive ihrer vollständigen Beobachtungsperiode** rückblickend eine MFE von mindestens 28 bp:

| Strategie | 2024 | 2025 |
|---|---:|---:|
| Pullback | 28,9 % | 26,3 % |
| Breakout | 29,6 % | 23,5 % |
| Mean Reversion | **51,0 %** | **40,1 %** |

Diese Größen sind **kein** Nachweis, dass das Ziel erst *nach* dem Stop erreicht wurde: Sie sagen lediglich, dass das Ziel innerhalb des vollständigen 60m-Fensters vorkam, obwohl der simulierte Trade zunächst ausgestoppt wurde. Der Zeitpunkt des maximalen MFE ist separat vorhanden. Ein hoher Anteil ist ein ernstzunehmender Anlass, die Bestätigungshypothese zu prüfen.

### 5.2 Peak-Timing

Median des 60-Minuten-MFE-Peaks 2025, gemessen in vollen 5m-Bar-Schritten ab Eintritt: Pullback **25 Minuten**, Breakout **20 Minuten**, Mean Reversion **20 Minuten**. Das ist nur eine rückblickende Zeitmarke. Sie sagt nichts darüber, ob vor diesem Peak bereits ein Stop ausgelöst wurde. 5m-OHLC zeigt keine genaue Tick-Sekunde.

## 6. Was können wir schon über Marktbedingungen sagen?

R14 speichert als **vorher bekanntes** Merkmal die vorherige 60m-Kursrichtung relativ zum Signal:

- **Breakout** ist per Regel stets mit der Stundenrichtung ausgerichtet; daher liefert „mit/gegen 60m“ **keine unabhängige Trennung** innerhalb dieser Strategie.
- **Pullback**: 2024 war die gegenläufige Gruppe etwa −14,14bp und die konforme etwa −15,00bp; 2025 −13,91bp versus −14,12bp. Alle Gruppen negativ. Ein Stundenrichtungsfilter alleine löst das Problem nicht.
- **Mean Reversion**: Die mit der Stundenbewegung ausgerichtete Gruppe ist klein (2024 nur **93** Signale, 2025 **264**), die Ergebnisse wechseln 2024/2025. Aus diesen Untergruppen darf kein robuster neuer Filter abgeleitet werden.
- **Tageszeit, Volatilitätszustand, vorangegangener mehrtägiger Preisbereich, mehrfache Zonentests, Handelsvolumen und echte Struktur-Rückeroberung** sind aus den R13/R14-Ereignistabellen **nicht vollständig rekonstruierbar**. Es existiert keine valide historische Zonen-Performance-Messung in den bisher hochgeladenen Daten.

## 7. Warum R15 genau die bestehende Forschungslücke schließt

R15 setzt eine besonders einfache, falsifizierbare Abfolge um:

1. Tagesbeginn: historische BTC-Hochs/Tiefs aus den **vollständig vergangenen 3, 14, 21 UTC-Tagen** einfrieren; Bänder von ±15 bp bilden.
2. Kontakt: Kurs nähert sich von außerhalb einem Band und berührt es. Sofort-Entry ist die **Referenz**, nicht die neue Strategie.
3. Reaktionsbestätigung: innerhalb der **folgenden drei geschlossenen 5m-Kerzen** schließt der Kurs außerhalb der Bandkante zurück in die erwartete Richtung, mit passendem Kerzenkörper und Schlusskursfortschritt. Nur dann Einstieg zum **nächsten Open**.
4. Stop strukturell knapp hinter dem tiefsten/ höchsten Kurs **bis einschließlich bestätigter Kerze**, zusätzlich 0,25 × ATR(14). Ziel 2R, Zeitlimit 120 Minuten. Beide Ansätze auf **derselben Zonengelegenheit** beobachten.
5. Kostenbasis 14 bp, Stress 24 bp; vollständiges First Touch mit konservativer Berührungskollision. Fehlende Bestätigung zählt **0 Trading-PnL pro Zonengelegenheit**, nicht als heimlich ausgeschlossener Verlierer.
6. 2024/2025 getrennt, dazu für jeden Zonentyp und Long/Short nur deskriptive Zahlen. **Keine nachträgliche Optimierung** und keine behauptete Blindtest-Sicherheit.

**Prüfbare Arbeitshypothese:** Die bestätigten Einstiege gewinnen nach modellierten Kosten im Durchschnitt mehr pro registriertem Kontakt als sofortige Einstiege. Um den Kandidaten weiterzuverfolgen, müsste in beiden Untersuchungszeiträumen der mittlere Nettoertrag **der tatsächlich bestätigten Trades** und der gekoppelte Vorteil **pro Kontakt** positiv sein, bei mindestens 100 bestätigten Trades je Zeitraum. Selbst dann ist lediglich eine Untersuchung auf **neuen, noch nicht untersuchten Marktdaten** gerechtfertigt.

### 7.1 Warum das noch kein endgültiger Strategietest ist

- 3-,14-,21-Tage-Extrema sind **vereinfachte** horizontale Zonen, nicht automatisch die diskretionär erkannten Konsolidierungs-/Reaktionszonen.
- Der feste ±15-bp-Bereich ist eine **Arbeitsannahme**. Wir optimieren ihn nicht nachträglich.
- Die Kontrollgruppe „sofortiger Eintritt“ ist vorab bekannt und zur gleichen Zonenberührung gepaart, damit keine Unterschiede in den Kontaktzeiten verfälschen.
- Ausgelassene Trades haben weder Gewinn noch Verlust; ein profitables kleines Subset kann völlig unzureichende Handelsfrequenz haben. Deshalb Bestätigungs- und Signalzahlen ausweisen.
- Kosten und Funding sind angenähert. Intrabar-Verlauf und Fill-Qualität bleiben unsicher.
- Überlappende bestätigte Ereignisse sind **nicht als realistisch simultan handelbares Kapitalportfolio** modelliert.
- Die historischen Jahre wurden in vielen früheren Studien betrachtet und können nicht durch ein neues Skript „wieder blind“ werden.

## 8. Umsetzung und Nachweise

Bereitgestellte Artefakte:

1. `R15_BTC_Zonen_Reaktion_Studienprotokoll_2026-11-15.md`: Phasen A/B mit eingefrorenen Regeln und Entscheidungskriterien.
2. `R15_BTC_Zonen_Reaktion_OneRun.py`: `--preflight` prüft synthetisch die First-Touch-Logik sowie Originaldatenprovenienz; `--run` erzeugt einmalig tatsächliche BTC-Ergebnisse. Bei bereits vorhandenem Resultatordner **Abbruch statt Überschreiben**.
3. Dieser Bericht: dokumentiert die **wirklich bereits gemessenen** R12–R14-Befunde, das noch offene R15 und dessen Interpretation.

Der Skriptcode wurde mit `py_compile`, synthetischen First-Touch-Tests und einem kompletten **künstlichen** Kursdatensatz probeweise ausgeführt. **Es wurde kein echter BTC-R15-Lauf in dieser Umgebung durchgeführt.**

## 9. Wie eine profitable BTC-Strategie daraus entstehen könnte

**Nur als Forschungspfad, keine derzeit nachgewiesene Strategie:**

- **Signal:** Rückkehr zu einer bereits bekannten Unterstützung / einem Widerstand, nicht blindes Gegenhalten während eines Impulses.
- **Eintritt:** Erst bestätigte Rückeroberung/Abweisung; frühestens nächster ausführbarer Open.
- **Risiko:** Strukturabhängiger Stop hinter tatsächlichem Reaktionstief/-hoch, nicht ein und derselbe Stop für Breakouts/Pullbacks/Reversions.
- **Gewinnmitnahme:** Vorab begründete 2R-Diagnose. Spätere TP-Anpassungen ausschließlich in einem neuen Forschungsdesign; nicht die größten historischen MFE-Peaks als Ziel übernehmen.
- **Marktbedingung:** Separate Beschreibung von Annäherung, Reaktion, fehlender Bestätigung, Trend-/Volatilitätskontext. Erst ein nachgewiesener inkrementeller Nutzen auf **neuen** Daten würde einen weiteren Filter rechtfertigen.
- **Validierung:** unabhängiger Zeitblock, verlässliche Gebühren und Funding, konservatives Intrabar, modellierte Orderfills, overlap-freie Portfolio-Simulation, schließlich isolierter Freqtrade-2026.9-Paper-Test, weiterhin ohne Live-Orders.

**Klares Entscheidungskriterium:** Ein schöner Chart, eine hohe MFE oder eine häufige Umkehr sind **nicht** profitabel. Profitabilität beginnt erst bei positiver, stabiler **realisierbarer Nettorendite** nach tatsächlich ausführbaren Ein- und Ausstiegen, zugehörigen Verlusten und Handelskosten.

## 10. Schlussfolgerung

Die Datenlage rechtfertigt **keine** Behauptung, dass eine profitable BTC-Strategie bereits gefunden wurde. Sie zeigt aber einen präzise begründeten Arbeitsansatz: Die bisher häufig viel zu frühen Mean-Reversion-Einstiege durch **vorab vorhandene Preisstruktur und erst danach beobachtete Kursbestätigung** ersetzen und **auf denselben Zonenkontakten gegen den sofortigen Einstieg vergleichen**. R15 wird genau diese neue Hypothese erstmals am historischen BTC-Markt messen, sobald der beigefügte Runner auf dem lokalen Datensatz ausgeführt wird.

## Fachgrundlage

- Carol Osler (2000), *Support for Resistance: Technical Analysis and Intraday Exchange Rates*, FRBNY Economic Policy Review. Empirische Ergebnisse in FX, **nicht** auf BTC automatisch übertragbar.
- Carol Osler (2003), *Currency Orders and Exchange Rate Dynamics*, *Journal of Finance*. Makro-/Mikrostrukturmechanismen der Zonen-/Stop-Clustering-Theorie.
- Bailey, Borwein, López de Prado & Zhu (2014), *Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance*. Warnung vor retrospektiver Siegerauswahl.
