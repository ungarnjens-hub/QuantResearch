# R7 – Phase-B-Audit: Inferenz für verschachtelte Modelle

**Stand:** 2026-11-14. **Status: KEINE PHASE-C-MESSFREIGABE.**

## Forschungsfrage des Audits

Sind die vorläufige R7-Entscheidungsregel (relativer MSE-Gewinn > 0, positives unteres 95%-Moving-Block-Bootstrap-Intervall und einseitiger Tages-HAC-p-Wert < 0,05) sowie eine Clark-West-adjustierte Tages-HAC-Diagnostik unter expliziter Null ohne zusätzliche BTC-Prognoseinformation plausibel kalibriert? Wie unterscheiden sich Größenordnung und Entdeckungsrate bei einem kleinen künstlichen Zusatzsignal?

**Wichtig:** Nur künstliche Daten. Hier wurden **keine Binance-Kurse** und keine R7-Marktprognosen ausgewertet. Die synthetische Untersuchung ist ein **reduziertes stündliches Regressionsmodell**, nicht die vollständige 5-Minuten-HAR-Merkmals-/RV-Zielkette. Ihre Testergebnisse übertragen sich daher nicht automatisch auf die spätere reale R7-Prozedur.

## Simulation (vor finaler Auswertung festgelegt)

- 300 unabhängige Simulationsläufe je Szenario, Seed 20261114 plus deterministische Offsets.
- 275 Trainingstage, 2.159 stündliche Testpunkte über 90 Kalendertage; Modellschätzung am Anfang und zu Monatswechseln.
- B2: Intercept + 6 künstliche Eigenmarkt-/SOL-Merkmale. M2: B2 + 3 künstliche BTC-Merkmale; OLS.
- Zeitlich persistente künstliche Faktoren und schwankende bedingte Fehlervarianz.
- Unadjustierte, gepaarte MSE-Differenz; 7-Tage-Moving-Block-Bootstrap auf Tagesaggregaten mit 1.000 Ziehungen; Tages-HAC mit 7 Lags.
- Zusätzlich: Clark-West-adjustierte Verlustdifferenz `e_B2² − e_M2² + (ŷ_B2−ŷ_M2)²`, einseitige Tages-HAC als **Diagnostik**, nicht als automatisch gültige formale Signifikanzentscheidung.
- Drei festgelegte Szenarien: (1) unabhängige zusätzliche Merkmale mit wahrem BTC-Koeffizienten null, (2) gemeinsame persistente Faktoren in Merkmalen mit wahrem BTC-Koeffizienten null, (3) gemeinsame Faktoren plus fixem kleinen Zusatzkoeffizienten 0,060 bei BTC-Merkmal 1.

## Ergebnisse aus der neu ausgeführten Simulation

| Szenario | Vorläufiges zusammengesetztes Gate | Roh-HAC p<0,05 | CW-HAC p<0,05 | Mittlere MSE-Änderung M2 vs. B2 |
|---|---:|---:|---:|---:|
| Unabhängige Null | 6/300 = 2,0 % | 8/300 = 2,7 % | 18/300 = 6,0 % | −0,0366 % |
| Korrelierte Null (gemeinsamer Faktor) | 1/300 = 0,33 % | 5/300 = 1,7 % | 21/300 = 7,0 % | −0,0415 % |
| Schwacher Zusatzkoeffizient | 111/300 = 37,0 % | 143/300 = 47,7 % | 275/300 = 91,7 % | +0,4187 % |

**Exakte binomiale 95%-Intervalle für das zusammengesetzte Gate:** unabhängige Null [0,74 %, 4,30 %], korrelierte Null [0,008 %, 1,84 %], schwache Alternative [31,52 %, 42,74 %].

### Interpretation

1. In **diesen beiden synthetischen Nullszenarien** produziert die vorläufige zusammengesetzte Regel weniger als 5 % positive Befunde im Punktschätzer. Daraus folgt **keine allgemeine Kontrolle** des Fehlalarmniveaus für reale Volatilitätsprozesse oder sämtliche Nullmodelle.
2. Die **CW-adjustierte Tages-HAC-Diagnostik** verwirft die Null in den beiden Beispielen 6 bzw. 7 % der Läufe. Insbesondere ist sie in dieser vereinfachten Implementierung **nicht** als bereits kalibrierter R7-Entscheidungstest freigegeben. CW korrigiert ein spezifisches Schätzrauschproblem verschachtelter Modelle, nicht automatisch sämtliche endliche-Stichproben-, Abhängigkeits- und Refit-Effekte.
3. Die *künstliche* schwache Alternative erzeugt im Mittel rund +0,42 % MSE-Verbesserung und wird vom konservativen zusammengesetzten Gate nur zu 37 % erkannt. **Unzureichende Power** ist damit eine ernsthafte Einschränkung: Ein nichtsignifikanter späterer Befund wäre kein verlässlicher Nachweis für das Fehlen eines kleinen Effekts.
4. Die simulierte Alternative ist **nicht** auf exakt 1–2 % Effektgröße kalibriert worden. Dafür ist ein **vorab definierter** weiterer synthetischer Versuchsplan erforderlich, keine nachträgliche Parameteranpassung nach Marktdaten.

## Im Audit entdeckter Simulationsfehler und Korrektur

Die **erste, ungültige Simulationsausführung** enthielt einen Innovationsfehler: Derselbe Zufallsschock wurde zugleich als Prädiktormerkmal und Zielstörung verwendet. Dadurch erschienen unter beiden Nullszenarien absurde scheinbare MSE-Gewinne von 82–92 % und 300/300 positive Gates. **Diese Ausführung wurde als fehlerhaft verworfen, nicht als Forschungsergebnis verwendet.** Das Skript wurde so korrigiert, dass die Zielstörung einen eigenen unabhängigen Innovationskanal erhält (13 statt 12 Zufallsspalten), und **alle 900 Simulationen erneut ausgeführt**. Die obige Tabelle stammt ausschließlich aus dem korrigierten Lauf. Dieser Fehler verdeutlicht, wie wichtig synthetische DGP-Audits selbst sind.

## Fachliteratur

- Clark & West (2007), *Journal of Econometrics* 138:291–311, DOI 10.1016/j.jeconom.2006.05.023: MSPE-adjustierte Tests bei verschachtelten Modellen; zusätzliche geschätzte Koeffizienten verursachen unter Null Prognoserauschen.
- Giacomini & White (2006), *Econometrica* 74:1545–1578, DOI 10.1111/j.1468-0262.2006.00718.x: Tests der bedingten Prognosefähigkeit; Ergebnisse für fixe rollierende Fenster sind nicht ungeprüft auf expandierende Monatsrefits übertragbar.
- Künsch (1989), *Annals of Statistics* 17:1217–1241, DOI 10.1214/aos/1176347265: Blockbootstrap für abhängige Beobachtungen.
- Neuere Literatur zur Bootstrap-Inferenz bei verschachtelten Prognosemodellen betont zusätzliche Hürden bei Mehrschrittzielen und serieller Korrelation (z. B. *Journal of Forecasting* 2023, DOI 10.1002/for.2987).

## Entscheidung / nächste Gates

**NO-GO für Phase C.** Die Ergebnisse rechtfertigen **keine** nachträgliche Testauswahl zugunsten von Clark-West oder des kombinierten Gates. Vor einer Messfreigabe sind nötig:

1. Reproduktion und unabhängige Prüfung des korrigierten synthetischen Codes, inklusive automatischer Tests gegen gemeinsame Ziel-/Prädiktorschocks und Zeitstempellecks.
2. Realistische, vorab spezifizierte **volle 5-Minuten-HAR-/log-RV-Kette** unter einer exakten bedingten Null, mit monatlichen Refits und clustered volatility; zusätzlich klar registrierte kleine Alternative und Sensitivität gegen Blocklänge/Regimewechsel.
3. Endgültige Festlegung, ob die rohe MSE-Intervallregel **primär** bleibt und welche sekundären p-Werte nur diagnostisch sind; Prüfung der Abdeckung und der Power im konkreten Design.
4. Prüfung des Trainings-/Testdatenregisters, des prospektiven Zeitfensters und sämtlicher Datenqualitätsgates erst nach bestandenem Methodenaudit; keine Vorabmessung von 2027-Marktdaten.

**R5/R6 unverändert. Keine TradingLab-, Paper-Bot- oder produktiven Dateien verändert.**
