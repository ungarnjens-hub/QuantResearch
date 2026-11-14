# R8 – Phase-A-Nachtrag v0.2: Korrelation und BTC→SOL-Lead-Lag

**Datum:** 14.11.2026  
**Status:** Forschungsdesign zur erneuten Phase-B-Prüfung. **Keine Freigabe für echte Marktdatenmessung.**  
**Verbindliche Vorgänger:** `R8_KORRELATION_UND_LEADLAG_PHASE_A_2026-11-14.md` (Commit `64ae5cf`), `R8_METHODENAUDIT_PHASE_B_2026-11-14.md` (Commit `a7f2a19`).  
**Änderungsgrund:** Schließen der Audit-Sperren; *keine* nachträgliche Änderung gemessener Ergebnisse. R7 und R5/R6 bleiben unberührt.

## 1. Forschungsumfang und primäre Hypothese

**R8-A (rein deskriptiv):** Pearson-Korrelation der synchronisierten 5-Minuten-Logrenditen von BTC–ETH, BTC–SOL und ETH–SOL auf Binance USD-M Perpetual Futures. Keine formalen Nullhypothesentests oder Auswahl des „besten“ Paares.

**R8-B (einziger primärer Test):** Enthalten die drei zuletzt abgeschlossenen BTC-5-Minuten-Renditen zusätzliche **Out-of-sample**-Information für das *Vorzeichen der folgenden SOL-5-Minuten-Rendite*, verglichen mit einem Modell, das nur die drei zuletzt abgeschlossenen SOL-Renditen kennt?

H0: Kein positiver OOS-Log-Loss-Gewinn des erweiterten Modells. H1: Positiver OOS-Log-Loss-Gewinn. Dies ist ein Test *bedingter Prognoseinformation*, kein kausaler BTC-First/SOL-Later-Nachweis.

## 2. Unveränderliche Daten- und Zeitdefinition

- Märkte: BTC/USDT, ETH/USDT, SOL/USDT; ausschließlich Binance USD-M Perpetual Futures, **last-trade**-5-Minuten-OHLCV-Kerzen.
- Rohzeitstempel `t` = UTC-**Öffnungszeit** der 5-Minuten-Kerze `[t, t+5min)`; vollständige Kenntnis erst bei `t+5min` (ggf. zusätzliche technische Latenz, im Audit dokumentieren).
- Rendite `r_t = ln(C_t / C_{t-5min})` ist als **Rendite zwischen den letzten beiden abgeschlossenen Kerzenschlüssen** definiert. Für jede Prognose bei Entscheidungszeit `T` sind die Merkmale aus den bis `T` geschlossenen Renditen `r_T, r_(T−5), r_(T−10)` zu berechnen, wobei das Symbol `r_T` der **zum Zeitpunkt T abgeschlossenen** Intervallrendite entspricht. In Roh-Open-Time-Daten gehört sie zur Zeile `T−5min`. Einheitlich in *Close-Time-Notation* implementieren.
- SOL-Ziel ist `r_SOL,T+5`, die Rendite der erst bei `T+5min` abgeschlossenen **nächsten** Kerze. Ein Label steht erst *nach diesem Schluss* zur Verfügung.
- Einheitliches vollständiges UTC-5-Minuten-Raster; **keine** impliziten Joins mit abweichenden Intervallen; keine Duplikate, keine selbst erfundenen Kerzen, kein Forward-Fill. Für Renditen über Lücken die Beobachtung und alle darauf beruhenden Lags ausschließen, mit vollständigem Zählprotokoll.
- Nur beim Entscheidungszeitpunkt tatsächlich verfügbare Daten verwenden. Gleiche abgeschlossene BTC- und SOL-Kerze zum selben `T` ist erlaubt, aber **kein Beleg**, dass BTC *innerhalb* dieses Intervalls zuerst reagiert.

## 3. R8-A: deskriptive Korrelation

- **Vorgeschlagener und ausdrücklich explorativer Zeitraum:** `2026-08-01T00:00Z` bis `2026-11-01T00:00Z` exklusiv (August–Oktober 2026). Dieser Abschnitt wurde in R5/R6 bereits verwendet und ist **kein Blindtest**.
- Genau drei Pearsons `corr(r_BTC,r_ETH)`, `corr(r_BTC,r_SOL)`, `corr(r_ETH,r_SOL)` auf derselben Schnittmenge gültiger synchroner Renditen; alle drei berichten.
- Vorzeichenübereinstimmung separat: Anteil gleicher Vorzeichen je Paar nur für Beobachtungen, in denen **beide** Renditen ungleich null sind; Nenner und verworfene Nullen angeben.
- Unsicherheit: synchron gepaarter Moving-Block-Bootstrap mit 7 **Kalendertagen** pro Block, 5.000 Ziehungen, NumPy `default_rng(20261114)`, 95%-Perzentilintervalle. Vor Aggregation vollständige und partielle Tage identifizieren; das genaue Resampling über Randtage ist im technischen Audit an synthetischen Daten festzulegen.
- Kein p-Wert, keine Rangliste der Gewinner, keine Kausalbehauptung. Konfidenzintervalle sind wegen historischer Vorselektion als deskriptive Unsicherheitsangaben einzuordnen.

## 4. R8-B: Binäre Definition und Baselines

**Nullrenditen-Policy, bewusst vor Datenblick beschlossen:** Das primäre Ziel ist `Y_T = 1` bei `r_SOL,T+5 > 0`, `Y_T = 0` bei `r_SOL,T+5 < 0`. Beobachtungen mit `r_SOL,T+5 = 0` werden **nur für den binären Score** ausgeschlossen und vollständig gezählt. Das ist ausdrücklich eine *bedingte* Aussage „Richtung **gegeben, dass eine Bewegung stattfindet**“. Der Ausschluss ist erst nach Realisierung des Zieles für die retrospektive Bewertung möglich; dadurch wird keine vollständig ex ante handelbare Binärprognose über **alle** Kerzen behauptet. Jede einzelne Prognose ist vor Einsicht in ihr Ziel zu erzeugen und zu speichern; erst danach wird die festgelegte Score-Maske angewandt. Anteil der Nullrenditen und Zahl aller vs. bewerteter Prognosen veröffentlichen.

- **B0 (diagnostisch):** Trainingsanteil `P(Y=1)` ohne Features, für jedes Refit ausschließlich aus bereits bekannten nichtnulligen Trainingslabels; Wahrscheinlichkeits-Log-Loss ausweisen.
- **B1 (primäre Baseline):** Unpenalisierte logistische Regression mit Intercept plus den drei letzten SOL-5-Minuten-Logrenditen.
- **M1 (primärer Kandidat):** Dieselbe logistische Regression plus drei vergangene BTC-5-Minuten-Logrenditen.
- **Keine weitere Feature-, Coin-, Horizont- oder Regime-Auswahl.** ETH gehört ausschließlich zu R8-A, nicht als Zusatzmerkmal in R8-B.
- Sämtliche Merkmale pro Refit ausschließlich mit Trainingsmittelwert und Trainingsstandardabweichung `z=(x−mean_train)/sd_train` standardisieren. Falls eine Trainingsspalte `sd=0`, ein Fit nicht konvergiert, eine Klasse fehlt, perfekte Separation oder numerisch nichtendliche Vorhersagen entstehen: **FAIL-CLOSED, keine Ersatzmodellsuche**. Der gesamte primäre Test gilt dann als technisch nicht auswertbar.
- Vorhersagen auf numerisches Intervall `[1e−12, 1−1e−12]` clippen **nur** zur endlichen Log-Loss-Berechnung; tatsächliche Clipping-Ereignisse erfassen.
- Im technischen Audit scikit-learn-/statsmodels-Versionskompatibilität und die tatsächlich unpenalisierte Schätzung verifizieren; Implementierungsdetails vor Messung hash-fixieren.

## 5. Zeitregister, Walk-Forward und Verbrauch

**Historisch bereits betrachtet:** R4 BTC→ETH 5m; R5/R6 BTC→ETH/SOL und insbesondere August–Oktober 2026; weitere frühere R1–R7 Untersuchungen sind vor der Messung im vollständigen Versuchsregister abzugleichen. Die Verwendung dieser Daten für das Design oder Training macht sie **nicht** zu einem neuen unabhängigen R8-B-Test.

**Für R8-B vorgeschlagener künftiger Blindtest:** `2027-04-01T00:00Z` bis `2027-07-01T00:00Z` exklusiv, 91 UTC-Kalendertage. Er liegt vollständig **nach** der für R7 reservierten Periode Januar–März 2027; keine Daten aus R7s reservierter Periode für R8 laden oder zum Training nutzen.

**Vorgeschlagenes Trainingsfenster:** `2025-01-01T00:00Z` bis `2027-01-01T00:00Z` exklusiv, mit verfügbarer gemeinsamer Markthistorie und rein historischen Labels. Darin darf Januar–Dezember 2026 nur als Training/Design gelten; November/Dezember 2026 sind heute noch keine verfügbaren vollständigen Daten. Bevor sie später eingelesen werden, muss die Phase-B-Freigabe erfolgen. **Keine** rückwirkende Modellwahl anhand dieser Abschnitte.

**Sperrintervall:** `2027-01-01` bis `2027-04-01` exklusiv: für R8 weder Training noch Test noch Merkmalswarm-up oder Fehleranalyse. Deshalb dürfen Testprognosen nur entstehen, sobald im April ausreichend **neue** abgeschlossene BTC- und SOL-Kerzen für alle drei Lags vorhanden sind.

**Refits:** Initiales Modell mit Daten bis `2027-01-01T00:00Z` (exklusiv) und erneute Fits zum Beginn des Mai und Juni 2027, wobei nur zum Refit bereits abgeschlossene und bekannte Labels aus dem April/Mai hinzugenommen werden. Der dreimonatige Sperrabschnitt bleibt ausgeschlossen. Prognosefrequenz 5 Minuten und exakter erster prognostizierbarer Zeitstempel werden per synthetischem Zeitachsen-Selbsttest festgelegt. Das erste Modell liegt für den April **ohne** Kenntnis der gesperrten R7-Periode vor.

**Ausfallregeln:** Jede regulär erwartete Prognose muss erklärt werden (gültig, technisch nicht möglich wegen fehlendem Lag, aus Datenlücke, noch unbekanntes Ziel, Null-Label nur im Score). Bei unerwarteten Lücken **kein** stilles Auffüllen und kein flexibles Verschieben von Testdaten. Ein unvollständiger Blindtest wird als *nicht vollständig auswertbar* dokumentiert.

## 6. Vorläufige Inferenz und Entscheidung

- Primäres Maß: `Δ = mean(LogLoss_B1 − LogLoss_M1)` über alle prognostizierten Testzeitpunkte mit **nichtnulligem** nachfolgendem SOL-Return. Positive Werte zeigen besseren M1-Score.
- Feste sekundäre Interpretation: relativer Rückgang des mittleren Log-Loss in %, B0-Log-Loss, Anteil Nullen, Zahl aller Prognosen, Anteil positiver Labels, Klassifikationsgenauigkeit (Schwelle 0,5; deskriptiv). Kein Ranking über Varianten.
- Unsicherheit: gepaarter Moving-Block-Bootstrap nach synchronen UTC-Kalendertagen, 7-Tage-Blöcke, 5.000 Ziehungen, Seed `20261114`, primäres 95%-Perzentilintervall für **absolute** Log-Loss-Differenz. Tage müssen als identische Paare resampelt werden; pro gezogenen Tag vollständige *Summen und Nenner* verwenden (keine ungewollte Tagesgleichgewichtung bei ungleicher gültiger Prognosezahl).
- **Vorläufiges Gate:** Nur wenn `Δ>0` und die untere 95%-Intervallgrenze >0, als *prospektive statistische Stützung* bezeichnen. Ist obere Intervallgrenze <0, als negative Evidenz gegen den spezifischen Vorteil bezeichnen. Sonst *ungeklärt*. Dieser Gate-Ansatz muss im synthetischen Nullkalibrierungstest mit **vollständiger Refit-/Feature-Pipeline** bestehen; andernfalls vor dem Blindtest die Inferenz vorab überarbeiten und erneut auditieren.
- Vorzeichenübereinstimmung bei Lag +1 und optionaler BTC→SOL-Korrelation sind **rein deskriptiv** und werden nicht als zusätzliche alternative Erfolgsentscheidung herangezogen.
- Keine Kausalitäts-, Profitabilitäts- oder Orderausführungsbehauptung.

## 7. Erforderliche Phase-B-Freigabepunkte

1. Vollständiges Datenverbrauchsregister einschließlich R4–R7 und der verbindlichen Reservierung von Januar–März 2027.
2. Nachweis, dass Testzeitraum April–Juni 2027 tatsächlich unverbraucht bleibt und kein nachträglicher Wechsel erlaubt wird.
3. Technischer Synthetic-End-to-End-Test für UTC-Open→Close-Semantik, Monatsgrenzen, Sperrfenster, Feature-/Label-Verfügbarkeit, unpenalisierten Logit, Zero-Return-Maske, NaN-/Lücken-Sperren, Tagesblockbootstrap.
4. Realistische synthetische Nullszenarien mit gemeinsamer Abhängigkeit/Clustering und **vollständiger** Prognose-/Refit-Prozedur sowie dokumentierten Fehlalarmraten und begrenzter Power.
5. Versionierte Implementation mit Quellcodehash, Bibliotheksversionen, Datenmanifest, Qualitäts-Gates und expliziter einmaliger Freigabe. Produktive TradingLab- und Paper-Bot-Dateien bleiben unberührt.

**Aktuelle Entscheidung: NO-GO Phase C.** Die Datumswahl ist ein Vorschlag und wird erst nach dem abschließenden Methodenaudit verbindlich. *Keine echten Marktdaten ausgewertet.*

## 8. Fachliche Grundlagen

- Granger, C. W. J. (1969), *Investigating Causal Relations by Econometric Models and Cross-spectral Methods*, Econometrica 37, 424–438; DOI `10.2307/1912791`.
- Jia, Y., Wu, Y., Yan, S., Liu, Y. (2023), *A seesaw effect in the cryptocurrency market: Understanding the return cross predictability of cryptocurrencies*, Journal of Empirical Finance 74, 101428; DOI `10.1016/j.jempfin.2023.101428`.
- Giacomini, R., White, H. (2006), *Tests of Conditional Predictive Ability*, Econometrica 74, 1545–1578; DOI `10.1111/j.1468-0262.2006.00718.x`.

**Gültigkeit:** Ergänzung zu R8 Phase A; frühere Dateien werden nicht überschrieben. Etwaige Änderungen nach Datenblick sind nur als neue explorative Version zulässig, nicht rückwirkend als vorregistriert.
