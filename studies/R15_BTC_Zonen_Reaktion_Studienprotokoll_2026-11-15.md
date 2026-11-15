# R15 | BTC-Futures: Vorher bekannte Preiszonen, Reaktionsbestätigung und First Touch

**Status:** Phase A Forschungsdesign und Phase B Code-/Methodenvorprüfung, vor echter BTC-Zonenmessung eingefroren. Die Datenjahre 2024 und 2025 sind schon aus R10–R14 exploriert: **keine unabhängige Validierung**.

## Fragestellung
Verbessert eine einfache, erst nach dem Zonen-Kontakt beobachtete Reaktionsbestätigung den simulierbaren **Nettoerwartungswert je Handelsgelegenheit** gegenüber dem sofortigen Einstieg beim Kontakt mit einer bereits am Tagesbeginn bekannten BTC-Preiszone?

## Fachlicher Marktmechanismus
Historische Preisniveaus können als Orientierung für limitierte Kauf-/Verkaufsbereitschaft, Gewinnmitnahmen oder Stops dienen. Empirische FX-Forschung von Carol Osler dokumentiert solche Mechanismen, beweist aber **keinen** Vorteil in BTC-Perpetuals. Die Operationalisierung mit Rückblickhochs/-tiefs ist eine prüfbare Annäherung an den Mechanismus, keine nachgewiesene Orderzone.

## Daten und Provenienz
Binance USD-M BTC/USDT lineares Perpetual, 5m last-trade OHLCV, 16 kanonische Monatsparquets 2024-09 bis 2025-12, laut vorhandenen R12-Prüfungen 140.256 geschlossene Kerzen. Daten werden **nur gelesen**; der zu R12 gehörende eingefrorene Datenloader muss SHA-256 `7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d` erfüllen. Zeitstempel sind UTC und 5m bar-open; eine Signalbedingung an Kerze j wird frühestens zur Öffnung von j+1 umgesetzt.

## Vorab feste Regeln (nicht optimiert)

1. **Zonen**: Für jeden UTC-Tag aus ausschließlich **vorangegangenen** vollen UTC-Tagen die maximalen Highs/minimalen Lows der letzten **3, 14, 21 Tage**, je ein Unterstützungs-/Widerstandsband um jedes Level mit fixer halber Breite **15 Basispunkte**. Keine Swing-Pivot-Markierung mit erst später bekannten rechten Nachbarkerzen. Dieses einfache Level-Modell bildet **nicht** alle diskretionären Preiszonen ab.
2. **Kontakt**: Schlusskurs der vorherigen 5m-Kerze oberhalb der Unterstützung beziehungsweise unterhalb des Widerstandsbandes; die jetzige Kerze berührt das Band. Auswahl eines Ereignisses bei Mehrfachkontakt: nächstgelegenes Vor-Kontakt-Level, danach längster Rückblick. Nach einem registrierten Ereignis **24 Bars Cooldown** (2h), keine Vollzählung aller möglichen Kontakte.
3. **Sofortige Referenz**: Einstieg zur nächsten 5m-Öffnung nach der Kontaktkerze in Richtung Rückkehr vom Level (Unterstützung Long, Widerstand Short).
4. **Bestätigung**: In den **nächsten drei abgeschlossenen 5m-Kerzen** ein Kerzenschluss **außerhalb** der Bandgrenze in Reaktionsrichtung, positive/negative Kerzenkörperrichtung und Schlusskursverbesserung gegenüber vorheriger Kerze. Schluss j+k j+k+1 open als frühester Einstieg. Ein Schluss jenseits der gegenüberliegenden Bandgrenze vor Bestätigung verwirft den Kontakt. Kein Bestätigungssignal: keine Position, aber die Begegnung bleibt für Opportunitätsbewertung im Nenner.
5. **Strategietypischer Struktur-Stop**: Long unter dem Tief der bereits bekannten Kontakt-bis-Bestätigungs-Kerzen minus 0,25 × ATR(14) auf der Bestätigungskerze. Short spiegelbildlich oberhalb des Hochs. Sofortige Referenz nutzt Tief/Hoch der Kontaktkerze und denselben ATR-Puffer. Ungültiger Abstand oder Stoppreis führt zum Auslassen des Kandidaten.
6. **Take-Profit**: fester 2R-Abstand vom realistisch modellierten Einstiegspreis; maximal 24 Fünf-Minuten-Kerzen (120 min), dann Ausstieg zur nächsten Öffnung. Stop/Gewinnziel: chronologischer erster Treffer; bei beidem innerhalb derselben Kerze konservativ **Stop zuerst**; schlechte Opening-Gaps zum Open, günstige Ziel-Gaps höchstens zum Ziel.
7. **Kosten**: Basis pauschal 14 bp, Stress pauschal 24 bp für den ganzen Trade. Gebühren/Slippage/Funding sind Modellannahmen, keine echten Funding-Zahlungen oder ausführbaren Orderbuch-Fills.
8. **Positionen**: Jeder registrierte Kontakt wird als unabhängig signalisierter Vergleich beobachtet. Überlappende Positionen zwischen Kontakten sind möglich. Das ist **kein Portfolio-Backtest** und keine Orderausführung.

## Messgrößen und Null-/Vergleichsmodell

- Anzahl registrierter Zonenkontakte, Bestätigungsrate, Auslassungen und Signalhäufigkeit.
- Für identische Zonenkontakte: Referenzeinstieg sofort; bestätigter Einstieg nur falls Bestätigung auftritt.
- Je tatsächlich ausgelöstem Trade: Brutto-/Netto-bp, Treffer-/Stop-/Zeit-Exit, Profit-Faktor, Median struktureller Stopbreite in bp, Zeit bis Ausstieg.
- **Primärvergleich je Zonenkontakt**: bestätigte Netto-bp bei erfolgter Bestätigung, ansonsten 0, abzüglich sofortiger Netto-bp beim Kontakt; tägliche Paare bleiben zusammen. Dieser Wert ist eine bedingte Gelegenheitsrendite, **keine** realistische Portfolio-Ertragsrate (überlappende Eintritte / ignorierte Kapitalbindung).
- Deskriptives paarweises 7-Tage-Blockbootstrap für Unterschiede je Zonenkontakt (1000 Wiederholungen). Wegen mehrfach untersuchter Daten, Modellannahmen und Abhängigkeiten **nicht kalibrierte Inferenz**, kein gültiger Signifikanzbeweis.
- 2024 Sep–Dez und 2025 Jan–Dez getrennt; deskriptive Unterschiede zwischen 3-,14-,21-Tages-Leveln sowie Long vs Short ohne automatische Filterselektion.

## Ex-ante Entscheidungsregeln

- **Keine Bestätigung / nicht bestätigt:** Eine bestätigte Einstiegsausführung zeigt in einem oder beiden Zeiträumen keine positive durchschnittliche modellierte Nettorendite; oder der Paarvergleich je Zonenkontakt ist nicht in beiden Zeiträumen positiv. Dann keine Wirtschaftlichkeitsbehauptung, Ansatz archivieren.
- **Explorativ weiter prüfen:** In **beiden** Zeiträumen mittlerer Nettogewinn je bestätigtem Trade und mittlerer Paarvorteil je Kontakt positiv; hinreichend Fälle (mind. 100 bestätigte Trades pro Zeitraum), keine extreme Ausführungs-/Ambiguitätslast. Auch dann **nur Kandidat für neues, nicht verbrauchtes Testmaterial**, keine „profitable Strategie“.
- **Vorläufig unklar:** Zu wenig Fälle, unzureichende Marktdaten, Instabilität, massive Intrabar-Konflikte, widersprüchliche Ergebnisse oder nicht validierte Handelskosten.
- Kein nachträgliches Anpassen der 15bp-Zonenbreite, Bestätigung oder Stop-/RR-Horizontes und anschließendes Ausgeben als ursprünglichen R15-Erfolg. Neue Varianten benötigen neues Forschungsprotokoll und neue, wirklich unabhängige Daten.

## Methodenaudit und Grenzen

- **Causality**: Die Zonen pro Kalendertag nutzen ausschließlich vergangene volle Tage; der Kontakt ist am Ende seiner Kerze bekannt, die Bestätigung erst nach deren Schluss. Die Exits beginnen ab dem tatsächlichen nächstkerzigen Einstieg.
- **Auswahlverzerrung**: Bestätigte Trades sind eine Teilmenge, daher sowohl conditional per-trade als auch unconditional per-contact ausweisen. Ausgelassene Kontakte explizit zählen.
- **Zeitabhängigkeit**: Signalüberschneidungen, Marktdrift und Clustering. Tages-Blockbootstrap rein deskriptiv.
- **Marktregime**: Vorheriger 60m-Verlauf und ATR-Prozentwert bei Kontakt werden archiviert, nicht nachträglich zur filteroptimierten Strategie erhoben.
- **Bewusst enger Forschungsumfang**: 3/14/21-Tagesextreme statt horizontaler Swing-Konzentrationszonen, kein Zonenaltern, kein Orderbuch, kein Liquidations-/Open-Interest-Indikator, keine Echt-Funding-Flüsse, keine dynamischen Take-Profits, keine Ticksequenz.
- **Sicherheitsgrenze**: Isoliertes `~/QuantResearch/R15_BTC_ZonenReaktion/`; produktives TradingLab, Bots, Profile, externe Strategien und Daten bleiben unverändert.

## Reproduzierbarkeit

`R15_BTC_Zonen_Reaktion_OneRun.py --preflight` führt synthetische Tests und den originalen Datengate durch, misst aber keine Marktergebnisse. `--run` prüft den Datengate erneut und führt genau eine Messung aus. Der neue Ergebnisordner darf noch nicht existieren. Erzeugt `R15_ZONE_EVENTS.csv`, `R15_RESULTS.json`, `R15_REPORT.md`.

## Literatur (nicht als Übertragbarkeitsbeweis)

- Osler, Carol L. (2000), *Support for Resistance: Technical Analysis and Intraday Exchange Rates*, Federal Reserve Bank of New York, Economic Policy Review.
- Osler, Carol L. (2003), *Currency Orders and Exchange Rate Dynamics: An Explanation for the Predictive Success of Technical Analysis*, Journal of Finance 58(5).
- Bailey, David H. et al. (2014), *Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance*.
