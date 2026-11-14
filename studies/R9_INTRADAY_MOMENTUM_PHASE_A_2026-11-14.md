# R9 – Intraday-Momentum nach Volumenimpuls
**Forschungsdesign Phase A | 14.11.2026 | Version 1.0 | Keine Marktdatenmessung**

## Zweck und Grenzen
Untersucht wird **nur** eine falsifizierbare, potentiell wirtschaftlich relevante Renditeasymmetrie auf Binance USD-M Linear Perpetual Futures (BTC, ETH, SOL). Keine Entwicklung, Auswahl oder Ausführung einer Live-Strategie, kein Freqtrade-Backtest, keine Änderungen produktiver Systeme. Die Konfiguration wird vor Marktdatenzugriff auditiert (Phase B). Die hier genannten Schwellen sind vorab gewählte *Forschungskonventionen*, keine aus Quellen abgeleiteten Optimalparameter.

## Literaturgrundlage
1. Shen, Urquhart & Wang (2022), *Bitcoin intraday time series momentum*, Financial Review 57, 319–344, DOI 10.1111/fire.12290. Dokumentiert intraday Momentum, besonders bei hohem Handelsvolumen bzw. Volatilität, aber **nicht** diese genaue 5m-Definition.
2. Wen, Bouri, Xu & Zhao (2022), *Intraday return predictability in the cryptocurrency markets: Momentum, reversal, or both*, North American Journal of Economics and Finance 62, 101733, DOI 10.1016/j.najef.2022.101733. Dokumentiert sowohl Momentum als auch Reversal, abhängig u.a. von Liqudität und Sprüngen.
3. Zaremba et al. (2021), *Up or down? Short-term reversal, momentum, and liquidity effects in cryptocurrency markets*, International Review of Financial Analysis 78, 101908, DOI 10.1016/j.irfa.2021.101908. Größere liquide Coins unterscheiden sich von illiquiden Altcoins; Befunde überwiegend auf Tagesfrequenz, keine direkte 5m-Bestätigung.

## Falsifizierbare Hauptfrage
Hat ein **abgeschlossener** starker 30-Minuten-Preisimpuls mit erhöhtem 5m-Handelsvolumen eine positive zukünftige Rendite **in Impulsrichtung** über die nächsten 30 Minuten, verglichen mit passenden starken Impulsen **ohne** Volumenbestätigung?

- **H0:** Die mittlere signierte zukünftige 30m-Logrendite nach volumenbestätigten starken Impulsen ist **nicht höher** als nach starken Impulsen ohne Volumenbestätigung (Differenz <= 0).
- **H1:** Diese Differenz ist > 0.
- Zweite, **sekundäre** Frage: Ist die signierte zukünftige 30m-Rendite der volumenbestätigten Ereignisse > 0? (Die ökonomische Bewertung folgt erst später.)
- Der mögliche Mechanismus ist verzögerte Informationsverarbeitung/Orderflow-Persistenz; mögliche Alternative ist kurzfristige Liquiditäts-Reversion. Kein Kausalnachweis.

## Daten und Zeitpunkt der Information
- Ausschließlich rohe Binance USD-M Futures `last_trade`-OHLCV-5m-Kerzen, synchron pro Markt, `open_time` in UTC, Schlusszeit `open_time + 5m`.
- Ein Ereignis wird bei Schluss der Kerze mit 5m-Endzeit t definiert. Alle Merkmale verwenden ausschließlich Kerzen mit Schlusszeit <= t. Zukunftslabel `log(close[t+30m]/close[t])`, niemals zur Signalauswahl.
- Preis-, Zeitraster-, Duplikat-, OHLC-, Volumen-, Markt- und Hash-Audit vor Messung. Sonderfälle/Nullrenditen/Zeitfenster vorab registrieren.
- **Keine** erneut als „Blindtest“ deklarierten Daten aus den 2026-Aug–Okt R5/R6/R8-Analysen. Chronologische Entwicklungs-/Auswertungs-/finale Holdout-Zeiträume erst nach vollständigem Bestands- und Verbrauchsregister festlegen, ohne die Testwerte einzusehen. Bereits analysierte Jahre/Teilstrecken bleiben „explorativ“.

## Vorab fixierte Ereignisdefinition (Phase B auf Korrektheit prüfen)
An jedem 5m-Schlusszeitpunkt t:
- `r30(t) = log(C_t/C_{t-30m})` (sechs abgeschlossene 5m-Schritte).
- `sigma5(t)` = Stichprobenstandardabweichung der 288 vollständig abgeschlossenen 5m-Logrenditen, die **vor Beginn** der 30m-Impulsperiode liegen; 288 Renditen entsprechen 24h. Bedingung `sigma5 > 0`.
- `z(t) = abs(r30(t)) / (sqrt(6)*sigma5(t))`. Ein **starker Impuls** liegt bei `z >= 2.0` vor; Richtung = `sign(r30)`, Null-Impuls ist nicht zulässig.
- Volumenverhältnis `v(t) = sum(volume der letzten sechs 5m-Kerzen) / (6 * Median(5m-Volumen der 288 vorangegangenen Kerzen))`, bei positivem Nenner.
- **M1:** starke Impulse mit `v >= 1.5`; **B1 (Kontrolle):** starke Impulse mit `v < 1.5`. Die Vergleichsgruppe wird auch hinsichtlich Impulsstärke und UTC-Tageszeit beschrieben, da Gruppen sonst nicht vergleichbar sein müssen.
- Um überlappende Labels zu verhindern: Pro Markt Auswahl in strikt zeitlicher Reihenfolge, nach registriertem Ereignis keine weiteren Ereignisse für die folgenden sechs 5m-Schlusszeitpunkte; diese Sperre gilt für **beide Gruppen gemeinsam**. Dieses Sampling ist Bestandteil des Forschungsprotokolls und darf nicht nach Ergebnis geändert werden.
- Das primäre Ziel `Y = sign(r30(t))*log(C_{t+30m}/C_t)` als Logrendite; Schlusskurs-zu-Schlusskurs ist **nur** ein Marktmechanismus-Proxy und keine ausführbare Rendite (Ausführung erst nach erkanntem Schluss, Spread/Slippage/Fees/Funding fehlen).

## Vergleiche, Inferenz, Interpretation
- Primär pro Markt `Delta = mean(Y|M1) - mean(Y|B1)`. Rohmittelwerte, Mediane, Anzahl Ereignisse und 30m-Vorzeichenquote je Gruppe zeigen; Imbalance und die Verteilung von `z`, Uhrzeit, Volumen separat berichten.
- Bei systematisch unterschiedlichen Verteilungen von Impulsstärke/Tageszeit gilt der rohe Vergleich **nur als bedingte Assoziation**, nicht als isolierter Volumeneffekt. Matching/Regression ist **nicht** stillschweigend erlaubt; dies wäre ein registrierter Folgeversuch mit eigenen Daten.
- 7-UTC-Tage-Blockbootstrap, 5.000 Ziehungen, Seed 20261114, 95%-Perzentilintervalle auf **Kalendertagsebene**, resample zeitlich zusammenhängende Tagesblöcke. Gruppen-Ereignisse innerhalb gezogener Blöcke zusammen resamplen; bei leerer Gruppe Test nicht auswertbar, nicht auffüllen oder retunen. Effektgrößen in Logrendite und Basispunkten; Unsicherheit und effektive Stichprobengröße transparent.
- Drei Asset-Tests bilden eine Familie; Holm-Anpassung nur für zuvor definierte Tests und **nur wenn** eine methodisch gültige p-Wert-Generierung festgelegt wurde. Andernfalls keine Signifikanzbehauptungen allein aus Bootstrap-CIs.
- Zusätzliche deskriptive Kontrollauswertungen nach Monat, Volatilitätszustand und UTC-Stundenblock **ohne** Neuoptimierung; keine Ergebnisse daraus als neuen vorab spezifizierten Haupteffekt ausgeben.
- Ein einzelnes Asset mit robust positivem Delta wäre ein Kandidat zur **weiteren unabhängigen** Überprüfung, kein Trading-Beweis. Negative/uneindeutige Resultate genauso archivieren.
- Nach erfolgter Forschungsbestätigung sind realistische, kausal ausführbare Entry-/Exit-Preise, Taker-/Maker-Gebühren, Spread, Slippage, Funding und Liquidität ein **separat zu genehmigendes** Forschungsdesign; ohne diese Prüfung keine Profitabilitätsaussage.

## Vor Phase B offene Pflichtpunkte (nicht überspringen)
1. Inventar: vorhandene historische Daten, echter Zeitbereich, bereits verbrauchte Perioden, Quellhashes; keine Daten „blind“ nennen, nur weil sie alt sind.
2. Prüfung der Volumenmetrik (Trade-Volumen in Basiscoin; keine börsenübergreifende Standardisierung behaupten), bei Datenlücken/Nullvolumen und Nachlaufgrenzen.
3. Audit der Ereignis-Sperrregel: Sie kann Kontrollgruppen und Gruppenzusammensetzung beeinflussen; Sensitivität **nicht** anhand des Testresultats optimieren.
4. Methodisch überprüfen, ob 7d-Blockbootstrap, mögliche ungleiche Gruppenstärken und >0-Test valide inferenziell interpretiert werden dürfen. Null-Tests auf synthetischen Daten vor echten Ergebnissen.
5. Daten-/Zeitfensterplan samt endgültigem unabhängigen Holdout und Erfolgskriterien einfrieren; nur ein später genehmigter Lauf von Phase C.

## Entscheidung
**Phase A vorbereitet. Phase B noch offen. Phase C NICHT freigegeben.**
