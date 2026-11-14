# R8 – Gleichlauf und möglicher zeitlicher BTC→SOL-Vorlauf

**Datum:** 14.11.2026  
**Status:** Phase A (Forschungsdesign), **keine Messfreigabe**.  
**Unabhängig von R7**: R5/R6 bleiben unverändert. Die für R7 erwogene Periode Januar–März 2027 wird für R8 **nicht** beansprucht.

## 1. Warum diese Untersuchung?

Die Beobachtung „BTC, ETH und SOL bewegen sich häufig in dieselbe Richtung“ betrifft *gleichzeitige Renditekorrelation*. Die Aussage „BTC bewegt sich zuerst, SOL folgt fünf Minuten später“ ist dagegen eine *gerichtete Prognosehypothese*. Beides darf nicht gleichgesetzt werden.

**Wissenschaftliche Grundlage:** Granger (1969) trennt prognostische Zeitrichtung von struktureller Kausalität. Jia et al. (2023, *Journal of Empirical Finance*, DOI 10.1016/j.jempfin.2023.101428) berichten, dass intraday Renditevorläufe in Kryptowährungen auftreten können und auch negativ sein können. Daraus folgt keine Vorfestlegung auf BTC als Führungsmarkt.

## 2. Zwei getrennte Fragestellungen

### R8-A: Deskriptiver Gleichlauf

- **Frage:** Wie stark korrelieren die *gleichzeitigen* logarithmischen 5-Minuten-Renditen von BTC/USDT, ETH/USDT und SOL/USDT auf Binance USD-M Futures?
- **Messgröße:** Pearson-Korrelation der drei vorab benannten Paare BTC–ETH, BTC–SOL und ETH–SOL, inklusive blockbootstrapbasierter Unsicherheitsintervalle; ergänzend Anteil gleicher Vorzeichen ausschließlich bei von null verschiedenen Renditen.
- **Hypothese:** Positive zeitgleiche Korrelation. Dies ist **deskriptive Evidenz**, kein Richtungs- oder Lead-Lag-Nachweis.
- **Diagnose:** Einheitliche abgeschlossene Zeitintervalle, identische Zeitzone, Preisdefinition und Schnittmenge gültiger Kerzen; Umgang mit Ausfällen und Nullrenditen vorab fixieren.
- **Keine Optimierung** über Zeitrahmen, Volatilitätsschwellen oder einzelne Tage.

### R8-B: Ein präregistrierter Prognosevergleich

- **Primäre Zielgröße:** Vorzeichen der *nächsten abgeschlossenen* 5-Minuten-Logrendite von SOL, beobachtet nach dem gemeinsamen Informationsstichtag. Zieldefinition und handelbare Verfügbarkeit müssen im Implementierungsaudit auf Kerzenebene getestet werden.
- **Nullhypothese H0:** Vergangene BTC-5-Minuten-Rendite liefert *keinen* zusätzlichen bedingten Out-of-sample-Prognosewert für das Vorzeichen der nächsten SOL-5-Minuten-Rendite gegenüber einer vorab definierten SOL-Eigenhistorien-Baseline.
- **H1:** Die BTC-Ergänzung verbessert die prädiktive Güte bedingt auf die SOL-Eigenhistorie.
- **Baseline:** Penalitätsfreie logistische Regression mit Intercept und den drei letzten abgeschlossenen SOL-5-Minuten-Renditen als Features.
- **Kandidat:** Exakt dieselbe Baseline plus die drei letzten abgeschlossenen BTC-5-Minuten-Renditen. Keine frei gewählten Schwellen, Parameter oder weiteren Märkte.
- **Primärmetrik:** Gepaarte OOS-Differenz der mittleren logarithmischen Verlustfunktion (Log-Loss, *Baseline minus Kandidat*). Positiv bedeutet Zusatznutzen.
- **Sekundär rein deskriptiv:** Genauigkeit vs. Mehrheitsklassen-Baseline, bedingter Anteil gleicher Vorzeichen und Korrelation bei Verzögerung +1 Kerze; nicht zur primären Entscheidung verwenden.
- **Nullrenditen:** Für die binäre Vorzeichenfrage vorab explizit definieren, insbesondere ob sie eine dritte Kategorie bilden oder ausgeschlossen werden. Solange diese Entscheidung nicht methodisch freigegeben ist, bleibt Phase C gesperrt.
- **Keine Kausalbehauptung:** Ein positives Resultat identifiziert weder wirtschaftlich verwertbare Latenz noch einen kausalen BTC-Impuls.

## 3. Verbindliche Methodengates vor Phase C

1. **Datenregister:** Welche lokalen historischen Abschnitte wurden in R1–R7 bereits betrachtet? Jeder dieser Abschnitte gilt für R8 als explorativ. Einen neuen unabhängigen Testzeitraum erst nach Bestandsaufnahme explizit festlegen; keine Doppelverwendung des für R7 reservierten Zeitraums.
2. **Datenprüfung:** Binance Futures-Preissemantik, UTC-Open-Time, Kerzenschluss, identische Handelsintervalle, Duplikate, Lücken, Missingness, warm-up und Rückrechnungsfreiheit.
3. **Zeitliche Trennung:** Feste chronologische Trainings-, Entwicklungs- und Testperioden, Walk-Forward-Refits und Purging an Prognosegrenzen. Keine Features oder Labels, die beim Prognosezeitpunkt unbekannt sind.
4. **Statistik:** Vorab geeignete Konfidenzintervalle und Tests für den abhängigen gepaarten OOS-Log-Loss festlegen; Cluster-/Blocklänge, Nachweisstärke und Null-Kalibrierung mit synthetischen Daten prüfen. Keine naiv unabhängigen 5-Minuten-Beobachtungen unterstellen.
5. **Mehrfachtests:** R8-A hat drei vorab benannte *deskriptive* Paare; R8-B hat genau einen primären Vergleich. Keine nachträgliche Auswahl des besten Coins, Zeithorizonts, Lags oder Marktregimes.
6. **Kontrolle allgemeiner Schocks:** ETH kann als vorab begründete *sekundäre Sensitivitätsanalyse* dienen, aber nur nach separater Registrierung und ohne die primäre R8-B-Entscheidung nachträglich umzudeuten.
7. **Fehlende Aussagekraft:** Wenn der Effekt klein oder das Intervall breit ist, lautet das Ergebnis „ungeklärt“ statt „existiert nicht“.
8. **Kein Profitabilitätsanspruch:** Slippage, Gebühren, Funding, Liquidität und tatsächliche Ausführung werden in dieser Untersuchung nicht bewertet.

## 4. Entscheidung

**Phase A erstellt. NO-GO für echte Marktdatenmessung.** Als Nächstes sind die Nullrenditen-Definition, Datenperioden, Validierungs- und Inferenzprozedur sowie ein unabhängiger Phase-B-Methodenaudit festzulegen. Produktive TradingLab/Freqtrade-Dateien und Paper-Bots bleiben unberührt.

## Literatur

- Granger, C. W. J. (1969), *Investigating Causal Relations by Econometric Models and Cross-spectral Methods*, Econometrica 37(3), 424–438; DOI 10.2307/1912791.
- Jia, Y., Wu, Y., Yan, S., Liu, Y. (2023), *A seesaw effect in the cryptocurrency market: Understanding the return cross predictability of cryptocurrencies*, Journal of Empirical Finance 74, 101428; DOI 10.1016/j.jempfin.2023.101428.
