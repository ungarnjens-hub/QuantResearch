# R8 – Methodenaudit Phase B (14.11.2026)

**Referenz:** `studies/R8_KORRELATION_UND_LEADLAG_PHASE_A_2026-11-14.md`, registriert in Git-Commit `64ae5cf`.

**Entscheidung:** **NO-GO für Phase C.** Die beiden Fragen sind sinnvoll und getrennt; das Phase-A-Design ist aber noch nicht ausreichend spezifiziert für einen unverzerrten, reproduzierbaren echten Datentest. Dieses Audit verändert die ursprüngliche Vorregistrierung nicht und führt keine Marktmessung aus.

## 1. Prüfung der wissenschaftlichen Grundlage

- **Granger (1969):** Zeitlich gerichteter Prognosebeitrag bedeutet nicht strukturelle Kausalität. Zulässig ist ausschließlich „inkrementelle Prognoseinformation“.
- **Jia, Wu, Yan und Liu (2023):** Die Veröffentlichung belegt, dass intraday Cross-Predictability in Krypto vorkommen kann; sie berichtet insbesondere einen **negativen** Seesaw-Lead-Lag-Effekt für größere gegenüber kleineren Coins. Sie darf nicht als Beleg für einen stets positiven BTC→SOL-Mitlauf ausgegeben werden.
- **Giacomini und White (2006):** OOS-Prognosevergleiche müssen die komplette Schätz- und Vorhersageprozedur berücksichtigen. Die konkrete Variante mit expandierender logistischer Regression darf nicht ohne Begründung als direkt von einem bestimmten asymptotischen Test gedeckt bezeichnet werden.

## 2. R8-A: Gleichzeitige Korrelation

**Methodisch geeignet:** Pearson-Korrelation synchronisierter 5-Minuten-*Logrenditen* für BTC–ETH, BTC–SOL und ETH–SOL; keine Korrelation der Kursniveaus. Der Gleichlauf der Vorzeichen ist nur ergänzende deskriptive Evidenz.

**Noch zu fixieren:**
1. Alle Renditen mit identischem Binance-USD-M-Futures-Markttyp und einheitlicher `last_trade`-Close-Definition auf UTC-Open-Timestamps. Rendite `r_t = ln(C_t/C_{t-1})` gehört zum Intervall, das an `t+5min` schließt.
2. Durchgängige Kalenderzeit mit Ausfall- und Duplikatprotokoll. Datenlücken nicht mit Forward-Fill künstlich schließen; für Renditen über Lücken eine Beobachtung als ungültig markieren und gemeinsame Zeitstempel verwenden.
3. Messzeitraum (einschließlich Forschungs-/Explorationsstatus) *vor* Berechnung fixieren. Frühere R1–R7-Zeiträume dürfen deskriptiv erneut genutzt werden, **nicht** als neuer Blindtest bezeichnet werden.
4. Festes CI-Verfahren für serielle Abhängigkeit: vorzugsweise gepaarter Moving-Block-Bootstrap auf synchronisierten Kalendertagesblöcken; feste Blocklänge, Ziehungszahl, Seed, Umgang mit Randtagen vor Messung registrieren. Alternative Sensitivitätsprüfungen vorher kennzeichnen.
5. Für die Hypothese „positive Korrelation“ klären, ob rein beschreibend oder formal testend. Drei formale Paarhypothesen erfordern vorab Multiplikitätskontrolle; als rein deskriptive Schätzungen keine Signifikanzsuche betreiben.

## 3. R8-B: gerichtete SOL-Richtungsprognose

**Grundvergleich passend:** Logistische Regression (SOL-Eigenhistorie) gegenüber derselben Regression + BTC-Vergangenheit; Log-Loss ist ein proper scoring rule für binäre Wahrscheinlichkeiten. Genau **ein** primärer Vergleich bleibt fixiert. **Wichtig:** Gute Klassifikationsgenauigkeit alleine ist kein Ersatz für den Log-Loss.

**Prüf- und Reparaturpunkte (Sperren):**

1. **Feature-Lag eindeutig:** Entscheidungszeitpunkt `T = Ende` der letzten gemeinsamen abgeschlossenen 5-Minuten-Kerze. Merkmale SOL `r_T, r_(T-5), r_(T-10)` und BTC `r_T, r_(T-5), r_(T-10)`. Ziel `sign(r_(T+5))` aus SOL. In Open-Time-Daten müssen `T` und `T+5` sauber umgerechnet werden. Nicht die teilweise laufende Kerze nutzen. Feature `BTC r_T` ist *gleichzeitig* mit `SOL r_T` bekannt und beweist keinen BTC-Vorsprung innerhalb dieser Kerze; geprüft wird Zusatznutzen für die **darauffolgende** Kerze.
2. **Nullrenditen:** Keine implizite Behandlung als negativ. Vorschlag für Phase-A-Nachtrag: `r_(T+5) = 0` separat zählen und diese Zeilen für den binären Primärtest ausschließen; **dies ist noch nicht freigegeben**. Eine Ausschlussregel konditioniert den Zielraum auf eine künftig eintretende Nicht-Null-Bewegung und begrenzt die Aussage. Alternativ drei Klassen oder vorher definierte Tie-Policy mit geeignetem Score. Auswahl *vor Datenblick* dokumentieren; verwendbare Vorhersagen dürfen nicht durch nachträgliche Zielprüfung für echte Anwendung missverständlich ausgegeben werden.
3. **Wahrscheinlichkeitsverfahren:** Keine Regularisierung laut Phase A. Vollständige/Quasi-Separation, singuläre Trainingsmatrix, nicht konvergierende Fits, fehlende Features und numerisch exakte Log-Loss-Berechnung (`eps`/Clipping) sind vorab als deterministische Fail-Closed-Regeln zu registrieren. Kein Wechsel zu Ridge/LASSO nach Resultaten.
4. **Skalierung:** Prozent- bzw. Logrenditen sind klein. Fester numerischer Scaling-Ansatz je Feature auf ausschließlich *Trainingsdaten* fitten und beim Forecast einfrieren; keine Gesamtperioden-Standardisierung oder datenabhängige Nachwahl.
5. **Zeitvalidierung:** Datensatzregister mit Trainings-, Entwicklungs- und unberührtem Testfenster, inklusive R4 BTC→ETH und R5/R6-Verbrauch bis 31.10.2026 sowie R7-Reservierung Jan–März 2027. Nicht voraussetzen, dass ein anderer Zielmarkt frühere Daten automatisch wieder zu einem Blindtest macht. Fixe Mindesthistorie, Refit-Kadenz, Label-Verfügbarkeit (`T+5`) und vollständige Vorhersagesequenz vor Datennutzung registrieren.
6. **Baseline der Praxis:** Neben dem *primären* Modellpaar eine vorab fixierte, nicht zu optimierende konstante Trainings-Mehrheitswahrscheinlichkeit als beschreibende Referenz (Log-Loss und Klassenverteilung) ausweisen; nicht nachträglich zur primären Nullhypothese ändern.
7. **Abhängigkeit und Inferenz:** Gepaarte OOS-Log-Loss-Differenzen sind zeitabhängig. Feste primäre Effektschwelle, Richtung, 95%-Unsicherheitsintervall, Blocklänge/Bootstrapverfahren, Stichprobenumfang und Abbruchregeln vorab fixieren. Bei **verschachtelten Modellen** und geschätzten Wahrscheinlichkeiten die Kalibrierung unter synthetischer Null mit echter Walk-Forward-Fit-Prozedur prüfen; keine naive i.i.d.-t-Tests oder unbewiesene Berufung auf G-W. Ein unentschiedener Test wird als **ungeklärt** archiviert.
8. **Grenzen:** Ohne Orderbuch, Trade-/Quote-Zeitstempel und Kosten lässt sich aus einer 5-Minuten-Kerzenprognose kein ausführbarer BTC-First/SOL-Later-Trade ableiten. Gemeinsame Schocks oder Latenz im Sekundenbereich werden mit 5-Minuten-Kerzen nicht identifiziert.

## 4. Konkretes Go/No-Go

**PASS im konzeptionellen Teil:** Forschungsfragen sauber getrennt, Zielmarkt SOL und primärer Modellvergleich B1 versus M1 vorab festgelegt, geeignete Rendite- und Log-Loss-Maße.

**NO-GO für Messung wegen:** fehlender verbindlicher Nullrenditen-Policy; fehlendem exakten Zeit-/Datenregister; unfixiertem Walk-Forward-/Refit-Verfahren; ungeklärten numerischen Logit-Randfällen; nicht freigegebener Inferenz/Null-Kalibrierung; noch nicht geprüfter Rohdaten-Verfügbarkeit und -Qualität.

**Nächste Arbeitsstufe:** Versionierter **Phase-A-Nachtrag** nur zu diesen Punkten, anschließend synthetischer End-to-End-Selbsttest des R8-A/B-Readers und der OOS-Auswertung. Erst danach erneuter Phase-B-Freigabeentscheid. Keine echte Marktmessung, keine Änderung an TradingLab/Freqtrade/Paper-Bots.

## 5. Fachquellen

1. Granger, C. W. J. (1969): *Investigating Causal Relations by Econometric Models and Cross-spectral Methods*. Econometrica 37, 424–438. DOI `10.2307/1912791`.
2. Jia, Y., Wu, Y., Yan, S., Liu, Y. (2023): *A seesaw effect in the cryptocurrency market: Understanding the return cross predictability of cryptocurrencies*. Journal of Empirical Finance 74, 101428. DOI `10.1016/j.jempfin.2023.101428`.
3. Giacomini, R., White, H. (2006): *Tests of Conditional Predictive Ability*. Econometrica 74, 1545–1578. DOI `10.1111/j.1468-0262.2006.00718.x`.

**Reproduzierbarkeitsvermerk:** Dieses Dokument enthält ein reines Literatur-/Designaudit. Es wurden keine BTC/ETH/SOL-Renditen berechnet und keine Marktergebnisse beobachtet.
