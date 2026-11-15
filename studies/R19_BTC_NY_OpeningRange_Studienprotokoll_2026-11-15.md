# R19: Bitcoin Opening-Range-Breakout gegen Fehlausbruch um 09:30 New Yorker Zeit

**Explorative Phase A/B, eingefrorene Regeln vor der echten Marktuntersuchung. Keine Orders und keine Änderungen an produktiven Daten.**

## Forschungsfrage

Die R18-Analyse der Binance-BTC-Perpetual-5m-Daten (September 2024 bis Dezember 2025) zeigte die höchste der geprüften NY-Stundenranges für 09:30–10:30 New Yorker Ortszeit. Ob dieser Zeitraum einen wirtschaftlich realisierbaren Handelsvorteil enthält, ist unbekannt. Wir vergleichen deshalb *zwei klar definierte Marktmechanismen* nach **derselben** Eröffnungsspanne: Fortsetzung eines Ausbruchs (ORB) und Umkehr eines gescheiterten Ausbruchs (Fakeout). Kein Anspruch, dass eine der beiden Strategien profitabel sein muss.

## Falsifizierbare Hypothesen

- H1: Ein bestätigter Schlusskurs außerhalb der ersten 15 NY-Minuten bietet bei festem Stop/Target/Horizont eine durchschnittliche **positive Netto-Folgerendite** nach modellierten Kosten (Nullmodell: Erwartungswert pro Opening-Session <= 0).
- H2: Eine binnen der nächsten drei geschlossenen 5-Minuten-Kerzen erkannte Rückkehr *in* die Opening-Range ergibt, in Gegenrichtung gehandelt, eine positive Netto-Folgerendite je Opening-Session (gleiches Nullmodell).
- H3 (gepaarter Vergleich): Der Nettoertrag pro Eröffnungstag ist für Fakeout größer als für ORB, ohne die Tage ohne Trade auszublenden. Vergleiche zunächst pro Jahr getrennt.

Drei vorab feste Hypothesen, keine zusätzliche Schwellen- oder Zeitfensteroptimierung. 2024 und 2025 wurden bereits vielfach ausgewertet, deshalb **kein unabhängiger Holdout**. CI explorativ; keine bestätigende statistische Testaussage.

## Daten und Definitionen

- Einzige Börse: Binance USDT linear Perpetual, BTC 5-Minuten letzte gehandelte OHLCV, 16 monatliche unveränderte Originaldateien, 140.256 Kerzen; read-only SHA256-verifizierter R12-Loader.
- Zeitzonen: 5m-Quellzeiten UTC; Eröffnung **09:30 America/New_York**, DST mit `zoneinfo`. Nur NY-Montag–Freitag; NY-Börsenfeiertage noch nicht gesondert entfernt, deshalb „NY-Ortszeit-Eröffnungsfenster“ und keine kausale Aktieneröffnungszuordnung.
- Opening Range: Hoch/Tief der abgeschlossenen drei 5m-Kerzen 09:30–09:45 NY.
- Signal: **erste** abgeschlossene 5m-Kerze zwischen 09:45 und 11:30 NY, deren Close die Opening Range strikt über- oder unterschreitet. Bei erstem Close oberhalb: Aufwärtsausbruch, darunter Abwärtsausbruch. Maximal ein Signalereignis pro NY-Tag.
- **ORB**: Signal in Ausbruchsrichtung; frühester Entry **Open der nächsten 5m-Kerze**, Stop am Mittelpunkt der Opening Range, TP 1,5R, Timeout nächste Kerzeneröffnung nach 120 Minuten.
- **Fakeout**: Auf den obigen ersten Ausbruch muss innerhalb der nachfolgenden **drei** vollständig abgeschlossenen 5m-Kerzen ein Close **strikt innerhalb** der ursprünglichen Range folgen. Entry nächste Kerze in Gegenrichtung des ursprünglichen Ausbruchs. Stop jenseits des bis zur Bestätigung beobachteten Extrempunkts des ersten Ausbruchs, mit 0,1 × ATR(14) 5m (ATR nur aus abgeschlossenen Bars einschließlich der Bestätigung); TP 1,5R, Timeout 120 Minuten.
- Falls Stop ungültig relativ zum nächsten Open oder Daten unvollständig: kein Trade. Keine nachträgliche Suche nach Ersatzsignalen. Kein Handel ohne Signal.
- Bei Stop+Target innerhalb derselben 5m-Kerze: **Stop zuerst**; Stop-Gaps zum schlechteren Open, Target-Gaps zum Target. Alle offenen Entscheidungen nach tatsächlichem Kerzenschluss. Getestete Periodengrenze schließt unvollständige Trade-Zukünfte aus.
- Modellkosten Basisszenario **14 bp roundtrip**, Stress **24 bp** als pauschale Annahmen (Gebühr, Slippage, Funding-Puffer). Funding kein historischer Zahlungsfluss; Preisfüllungen sind 5m-OHLC-Approximation, kein Orderbuch.
- Pro Methode und pro Tag max. ein isolierter hypothetischer Trade. Die zwei Methoden werden **getrennt** simuliert, kein kombiniertes Portfolio und keine möglichen simultanen Positionen.

## Kennzahlen

- Handelstage, Breach-Häufigkeit, Ausführungen pro Strategie, Mittel brutto und netto pro tatsächlich ausgeführtem Trade sowie pro *allen* NY-Handelstagen (kein Signal = 0), PF nach modellierten Kosten, Stop/TP/Zeitablauf, Median strukturelles Risiko, Haltedauer, Kostenstress.
- Erste Signale 09:45–10:30 NY gegenüber 10:30–11:30 NY: **rein deskriptive** zeitliche Aufteilung, keine nachträgliche Wahl eines Siegerfensters.
- Tagesweise gepaarte Netto-Differenz Fakeout minus ORB und zirkulärer Tages-Blockbootstrap à 7 Handelstage, 2.000 Replikationen, feste Seed. Nur deskriptives 95%-Intervall, keine Multiplicity- oder Selektionskalibration.
- Ergebnisse 2024 Sep–Dez und 2025 Jan–Dez separat. Keine Optimierung nach Testergebnis und keine Umdeutung explorativer Schwellen als bestätigte Auswahlregeln.

## Vorabprüfung und Freigabe

1. Synthetische Prüfungen für New-York-Sommerzeit, Zeitpunkt der ersten fertigen Opening-Range, Intrabar Stop-vor-TP, Kosten, ungültige Preisgaps, maximalen Zeithorizont und E2E-Both-Signalbeispiel.
2. Unveränderter eingefrorener R12-Datenloader und monatliche SHA256-Provenienz; Data Gate vor Messung.
3. Forschungsdateien vor Messung in eigenem `studies/`-Verzeichnis committen; Ergebnisausgabe nur neu und getrennt unter `~/QuantResearch/R19_BTC_NY_Open/Sep2024_Dec2025_v1`.
4. Einmaliger `--run`. Keine wiederholten R19-Varianten nach Ergebniseinsicht ohne eigene neue Kennung und explizite Explorationsregistrierung.

## Entscheidung

Für irgendeine **profitable** Strategie braucht es positive Nettoresultate, robuste Kostenannahmen, einen von Null unterscheidbaren positiven Erwartungswert und einen vorab registrierten unabhängigen Blindtest. Auch dann sind Liquidität, Funding und Fill-Risiken zusätzlich zu berücksichtigen. Alle R19-Ergebnisse sind zunächst Forschungshinweise, keine Handlungsempfehlung.
