# R5/R6: Externe zeitliche Prognosevalidierung, Prüfprotokoll v1

**Erstellt:** 2026-11-14. **Status:** Phase B: Protokollentwurf und Audit, *keine Testdaten geladen, keine Ergebnismessung, keine Freigabe zum Test*. Die Regeln unten wurden vor einer neuen Auswertung der August–Oktober-Daten formuliert. Dieses Protokoll ist nicht rückwirkend die ursprüngliche R5/R6-Präregistrierung.

## Hypothesen und Marktmechanismus

Vergangene Volatilität von BTC enthält über die marktinterne HAR-RV-Dynamik hinaus zusätzliche Prognoseinformation für die realisierte zukünftige 60-Minuten-Volatilität von **ETH** und **SOL**. Der Mechanismus ist eine mögliche marktweite Informations- oder Volatilitätsübertragung, **keine nachgewiesene Kausalwirkung**. Je Zielmarkt lautet H0: mittlere gepaarte Differenz des quadratischen Prognosefehlers `d = (y-B1)^2-(y-M1)^2 <= 0`; H1: `E[d] > 0`. Beide Marktvergleiche werden ohne Selektion berichtet.

## Referenz und exakte Prognoseprozedur

Fixierte ursprüngliche R5-/R6-Implementierungen (Code und Hash vor Messung erneut nachweisen); **keine Parametersuche**. Binance USD-M Linear Perpetual, last-trade OHLCV, Kerzenöffnungszeit UTC, vollendete 5m-Kerzen. `r_t = log(close_t/close_(t-1))` (dabei ist `close_t` erst zum 5m-Kerzenende bekannt). Um 5m-Kerzenöffnung `t` mit `minute=55` werden Merkmale der letzten **abgeschlossenen** 12/288/2016 Renditequadrate benutzt: `log(mean(r²)+1e-12)`; die Forecastentscheidung für diese `t`-Kerze ist daher **erst an deren Abschluss `t+5 min`** verfügbar. Das Ziel `y_t = log(sum_(j=1)^12 r_(t+j)^2 + 1e-12)` verwendet die nächsten zwölf 5m-Renditen und wird *nicht früher als* `t+65 min` verfügbar. Für alle Märkte gilt:

- B0: historischer Mittelwert des verfügbaren logarithmierten Zieles.
- B1: OLS mit Intercept und Eigenmarkt-HAR 12/288/2016.
- M1: B1 mit zusätzlich BTC-HAR 12/288/2016.
- Trainingsstart 2024-09-01 00:00 UTC, mit Feature-Warm-up aus früheren Kursen; nach R5/R6 nur historische Daten mit `available <= Refit-Zeitpunkt`.
- Neufit jeweils am Monatsersten 00:00 UTC, expandierendes Training. Testprognosen des August dürfen für das September-Refit nach bekanntem Label benutzt werden; entsprechend September für Oktober. **Damit ist es eine sequenzielle, vorab festgelegte Out-of-sample-Prozedur, kein für drei Monate unverändert versiegelter Modell-Fit.** Testberichte dürfen vor Abschluss der drei Monate nicht eingesehen werden; Modell und Testregeln bleiben unverändert.
- Gemeinsamer vorgeschlagener Evaluationszeitraum `[2026-08-01 00:00, 2026-11-01 00:00)` UTC. Es zählen nur Prognosepunkte mit `available <= 2026-11-01 00:00 UTC`. Keine variable Wahl günstiger Tage, Stunden, Marktphasen oder weiterer Coins. Prüfdaten ab August müssen unabhängig von früheren R5/R6-Evaluationsdaten neu bezogen und als solche dokumentiert werden. Historische Datennutzung in anderen Programmen muss im Experimenteregister noch geprüft werden; keine kategorische Blindtest-Behauptung.

## Primäre Auswertung, Multiples Testen, Robustheit

Für jeden Markt alle zulässigen Prognosen: `MSE_B0`, `MSE_B1`, `MSE_M1`, `G = 100 * (MSE_B1-MSE_M1)/MSE_B1`, Fehlervarianz, n, Anzahl Wochen, exakte Zeitabdeckung. Primärer Test **je Markt** auf positive unadjustierte quadratische Verlustdifferenz d; da stündliche Fehler seriell korreliert sind, zuerst *je UTC-Kalendertag* die Summe d und Anzahl Vorhersagen erfassen; bei vollständiger vorab erwarteter Tagesabdeckung täglich mitteln (24 Prognosen pro Tag; **am letzten Tag 2026-10-31 nur 23**, weil die Prognose um 23:55 erst nach dem fixierten Endzeitpunkt als Ziel bekannt wäre). Erwartet werden daher **2207 Prognosen je Markt**, sofern sämtliche zugelassenen Zeitpunkte vorhanden sind. Für vollständig tagedeckende Tests die Tagesmittelwerte mit Intercept-only OLS und **Newey–West/HAC Bartlett, 7 Tageslags**, testen; einseitige Normalapproximation `p=norm.sf(z)`. Das ist ein vorab festgelegter **approximativer** Test, keine garantierte Klein-Stichproben-Inferenz. Wenn Tagesabdeckung nicht vollständig ist, ist die Validierung **nicht auswertbar**; Lücken werden nicht nachträglich herausgefiltert.

Zwei vorab festgelegte Markt-Hypothesen: Holm-Adjustierung der beiden einseitigen p-Werte bei familienweitem `alpha=0.05`. **Jeder Markt separat** gilt nur dann als *zeitlich vorläufig bestätigt*, wenn gleichzeitig `G>0`, `Holm-p<0.05` und die Untergrenze eines **vorab fixierten** gepaarten Moving-Block-Bootstrap-Intervalls für G > 0 ist. Unsicherheitsintervall: tägliche Paare `(sum e_B1², sum e_M1², n)` für die **92 Tage** August–Oktober; Moving-Block mit 7 aufeinanderfolgenden UTC-Tagen, 5.000 Resamples, MT19937/NumPy `default_rng(20261114)` (PCG64), 95% Perzentil, alle drei Monate zusammen; gleiche Ziehungsindizes für alle Modelle und Märkte zur Reproduzierbarkeit. **Warnung:** Bei nur 92 Tagen und rund 13 Wochen sind sowohl Bootstrap als auch HAC unsicher; die Intervalle sind approximativ. Die strenge kombinierte Regel ist eine vorsichtige Projektauswahlregel, kein etablierter einheitlicher Signifikanztest.

Fehlende erwartete Prognosen (Soll: 2207 pro Markt; letzter Tag 23 Prognosen), weniger als 90 vollständig erwartungsgemäß abgedeckte UTC-Tage, weniger als 12 abgedeckte Siebentageblöcke, inkonsistente Kerzenzeiten oder unvollständige BTC-/Zielmarkt-Historie: **nicht auswertbar**, fehlende Daten dokumentieren, keine stillschweigende Substitution. Sind die Daten vollständig, aber die kombinierte Regel nicht erfüllt: je nach Vorzeichen/Präzision *nicht bestätigt* bzw. *ungeklärt*. **Keine** neuen Fenster, andere Lags, Blocklängen, Proxy-Ziele, Modellvarianten oder Datenbereinigungen nach Kenntnis der Testwerte. Der historische Clark-West-HAC(4)-Wert wird höchstens deskriptiv sekundär reproduziert, **nicht** als primärer Test verwendet.

## Pflichtprüfung vor Datenzugriff / Phase-B-Gate

1. Forschungsregister **projektweit**, auch außerhalb `~/QuantResearch` und `~/Downloads/Marktforschung`, auf bereits verwendete August–Oktober-Daten, Kandidatenwahl und versteckte Evaluierungen prüfen. Die vorherige Suche in nur 35 Textdokumenten reicht **nicht** als Beweis der Unverbrauchtheit. Falls unbekannte Nutzung: Status auf `unabhängige Validierung nicht gesichert` setzen.
2. Literaturbezug und HAC-/Blocklängenaudit, insbesondere kleine effektive Wochen-Stichprobe dokumentieren. Bei Einwänden **vor** Datenzugriff eine neue dokumentierte Version erstellen und die alte behalten.
3. Datenbeschaffung **erst nach Gate**, in neuem isoliertem Ordner. Binance Futures 5m Last-Trade-Klines für BTC, ETH, SOL; Quellenendpunkt, Downloadzeit, Bytes, SHA256, UTC, Kerzenbeginn/-ende, `is_closed`, Duplikate, Lücken, plausible OHLC, gemeinsamen Zeitraum, Markttyp und Warm-up prüfen. Keine Befunde über Prognosegewinn sehen. Die bisherigen SOL-Quelldaten hatten keine vollständige externe Provenienz; neu abgerufene Daten sollen dies beheben.
4. Code-/Quellhashes, Versionsinformationen, Implementierungssynopse, synthetische Anti-Lookahead-Tests und stündliche Labelverfügbarkeitsgrenzen vorab protokollieren; bei Prüfungsfehler vor Messung STOP.
5. Einmalige vollständige Prognoseberechnung; R5 und R6 **beide** unverändert, kein Zwischenbericht, keine vorzeitige Testzeitwahl, kein Backtest einer Handelsstrategie.

## Wissenschaftlicher Rahmen

- Clark & West (2007), *Journal of Econometrics* 138, 291–311, DOI 10.1016/j.jeconom.2006.05.023 (verschachtelte Prognosemodelle).
- Giacomini & White (2006), *Econometrica* 74, 1545–1578, DOI 10.1111/j.1468-0262.2006.00718.x (Prognoseverfahren, Schätzunsicherheit; deren Haupttheorie beruht auf beschränkter Schätzmemory und kann nicht pauschal auf expanding-window-OLS übertragen werden).
- Harvey, Leybourne & Newbold (1997), *International Journal of Forecasting* 13, 281–291, DOI 10.1016/S0169-2070(96)00719-4 (Probleme kleiner Stichproben bei Prognosevergleichen).

## Governance

Forschung ausschließlich in `~/QuantResearch` mit Berichten/ZIPs unter `~/Downloads/Marktforschung`. Keine bestehenden R5/R6-Dateien, Tests, Bots, Konfigurationen oder Daten ändern. Originaldaten bleiben read-only. Alle Ergebnisse vollständig und unverändert archivieren. **Kein Zusammenhang mit erwiesener Profitabilität.**

**Freigabestatus:** NICHT FREIGEGEBEN. Nächster tatsächlicher Arbeitsschritt: Phase-B-Prüfung der Vollständigkeit des Forschungsregisters und Definition eines vollständigen, automatisierbaren Mess-Gates; keine Daten herunterladen oder analysieren, bevor dieses Gate bestanden ist.
