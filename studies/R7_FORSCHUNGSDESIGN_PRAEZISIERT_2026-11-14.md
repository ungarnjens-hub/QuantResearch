# R7 – Präzisiertes Forschungsdesign (Version 0.2)

**Stand:** 2026-11-14  
**Status:** Phase A überarbeitet, Phase B erneut zu auditieren; **keine Freigabe zur Ergebnismessung**.  
**Verweis:** `studies/R7_FORSCHUNGSDESIGN_PHASE_A.md`; `studies/R7_METHODENAUDIT_PHASE_B_2026-11-14.md` (Git-Commit `aa4002a`).

## 1. Präzise wissenschaftliche Frage

**Liefert vergangene BTC-Volatilität zusätzliche Out-of-sample-Prognoseinformation für die nächsten 60 Minuten der ETH-Volatilität, wenn neben ETHs eigener Volatilitätshistorie auch die vergangene SOL-Volatilität als begrenzter Proxy für marktweite Risiken berücksichtigt wird?**

Das ist ein Test *bedingter zusätzlicher Prognoseinformation*, **kein** Test struktureller Kausalität. Das Ziel wurde enger gefasst als der ursprüngliche R7-Entwurf, um ein primäres Prüfproblem statt einer ungeordneten Testserie zu haben.

**Vorregistrierte, gerichtete Arbeitshypothese H1:** Das Modell mit zusätzlichen BTC-HAR-Merkmalen erzielt geringeren mittleren quadratischen Prognosefehler als das Kontrollmodell ohne BTC-Merkmale.

**H0:** Kein positiver zusätzlicher OOS-Prognosewert gegenüber dem Kontrollmodell.

**Zielmarkt primär:** ETH. **SOL:** Nur Kontrollinformation; keine zweite primäre Zielmarkt-Hypothese. Die Wahl basiert auf bereits bekannten R5/R6-Befunden; diese Selektionsgeschichte muss berichtet werden.

## 2. Beobachtungen, Zeitstempel und abhängige Variable

- Binance USD-M lineare Perpetual Futures, 5-Minuten-OHLCV **Handelspreis** (`last_trade`), gleiche Venue und Preissemantik für BTC, ETH, SOL.
- Log-Renditen aus abgeschlossenen 5-Minuten-Schlusskursen.
- Prognoseentscheidung jeweils zur UTC-Stundengrenze **nach Abschluss** der 5-Minuten-Kerze mit Open-Time `hh:55`. Forecast-Index ist `hh:55`, aber Informationszeit ist **`hh+1:00`**. Diese Unterscheidung muss im Audit demonstriert werden.
- Prognoseziel: `log(sum_{j=1}^{12} r_ETH,t+j^2 + 1e-12)`. Erster Zielreturn liegt nach der jüngsten beobachteten Kerze; der letzte kommt aus der 60-Minuten-Folgeperiode.
- Alle Labels frühestens **65 Minuten nach dem Forecast-Index** verwendbar, entsprechend der bisherigen R5/R6-Codelogik.

## 3. Feststehende Merkmale und Modellvergleich

Merkmale zum Forecast-Index `t`, berechnet nur aus bis dahin abgeschlossenen Kerzen:

`HAR_X,k(t) = log(mean_{i=0,...,k-1} r_X,t-i^2 + 1e-12)`, `k ∈ {12,288,2016}` und `X ∈ {BTC,ETH,SOL}`.

- **B0 (Diagnostik):** Historischer Trainingsmittelwert des ETH-Ziels.
- **B1 (Diagnostik, R5-Baseline):** OLS-Intercept + ETH-HAR(12,288,2016).
- **B2 (primäre Kontrollbaseline):** OLS-Intercept + ETH-HAR(12,288,2016) + SOL-HAR(12,288,2016).
- **M2 (primärer Kandidat):** B2 + BTC-HAR(12,288,2016).

**Primärer Vergleich ausschließlich M2 gegen B2.** Keine weiteren Indikatoren, Verzögerungen, alternativen Märkte oder nachträglichen Variablenauswahlen.

Hinweis: SOL ist lediglich ein **unvollkommener Risiko-Proxy**. B2 kontrolliert weder alle gemeinsamen Schocks noch deren Echtzeitinformation vollständig. Negative Ergebnisse von M2 können zudem aus Multikollinearität resultieren. Weder positives noch negatives Ergebnis identifiziert den kausalen Ursprung der Volatilität.

## 4. Zeitreihenprotokoll – vorläufige Festlegung, noch zu auditieren

- **Vorgeschlagener, prospektiver Testzeitraum:** `2027-01-01T00:00Z` bis `2027-04-01T00:00Z` exklusiv (90 UTC-Tage).
- **Wissenschaftlich entscheidend:** Eignung und Unverbrauchtheit dieses Zeitraums *vor dem ersten Datenzugriff* prüfen und dokumentieren. Eine Neuauswahl des Zeitraums nach Ergebniskenntnis ist ausgeschlossen.
- **Trainingsbeginn:** `2024-09-01T00:00Z`, soweit die vorhandene gemeinsame Historie für BTC/ETH/SOL die festen 2016-bar-Fenster vollständig deckt; erster tatsächlich zulässiger Forecast und Trainingseintritt nur nach erfüllter Historie. Die verfügbare SOL-Historie beginnt später als die von BTC; die tatsächlich gemeinsame Startzeit muss dokumentiert werden.
- **Prognosefrequenz:** 1× je UTC-Stunde (nur `hh:55`-indizierte Forecasts), Ziele dürfen nicht hinter das Testende reichen.
- **Schätzung:** OLS mit Intercept, expandierendes Trainingsfenster, monatliches Refit zu 1. Januar / 1. Februar / 1. März 2027, ausschließlich Trainingszeilen, deren **Label zum Refit-Zeitpunkt verfügbar** ist.
- **Kein Look-ahead:** Keine Revision bisheriger Prognosen, kein erneuter Zugriff auf zukünftige Zielwerte bei einem Refit.
- **Unverändertes Forschungsdesign:** Vorbehaltlich bestandenem Audit gelten dieselben HAR-Fenster und dieselbe Zieldefinition wie R5/R6. Details der Datenübergabe und der Fehlerbehandlung sind vor Messung zu spezifizieren.

## 5. Primärmaß und Entscheidungsregeln – vorgeschlagen

- Einzelne Verlustdifferenz: `(y-B2)^2 - (y-M2)^2`. Positiv bedeutet besseren M2-Forecast.
- Primäre Effektgröße: `100*(MSE_B2 - MSE_M2)/MSE_B2` über **alle** zulässigen Prognosen.
- Primäre Unsicherheit: gepaarter Moving-Block-Bootstrap auf Kalender-Tagesblöcken, Blocklänge 7 Tage, 5.000 Ziehungen, fixer Seed `20261114`, 95%-Perzentilintervall.
- Sekundär: auf Tagesmitteln der Verlustdifferenz Newey-West/Bartlett-HAC mit 7 Tageslags und einseitigem p-Wert. Für diesen **einen** primären Vergleich keine Holm-Korrektur erforderlich; jeder zusätzliche Test wird *vorher* separat registriert und multiplicity-korrigiert.
- **Kriterium für „prospektiv gestützt“:** Positive MSE-Verbesserung **und** untere 95%-Bootstrap-Grenze > 0 **und** einseitiger HAC-p-Wert < 0,05. Bei widersprüchlichen Ergebnissen: *ungeklärt*, nicht nachjustieren.
- **Kriterium für „nicht gestützt“:** Effekt ≤ 0 oder obere 95%-Intervallgrenze < 0; sonst bei zu breiter Unsicherheit *ungeklärt*.
- Kein Mindestgewinn, keine Handelskostenrechnung, keine Strategie oder Orderausführung. Drei Monate / ca. 90 Tage sind eine begrenzte Inferenzbasis; bei unzureichender Evidenz nicht nachträglich verlängern.

## 6. Vor der ersten echten Messung zwingende Freigabepunkte

1. Dieses Dokument auf GitHub committen, den Commit-Hash protokollieren und mit dem Vorgänger-Audit abgleichen.
2. **Phase-B-Fachaudit:** Ist das konkrete Kontrollmodell B2 geeignet? SOL als Proxy rechtfertigen; verzerrende Gleichzeitigkeit und Informationszeit prüfen; die Grenze zwischen bedingtem Informationsnutzen und Kausalität präzise benennen.
3. Forschungsregister für R1–R6 und andere relevante Studien auf Nutzung von 2027-01 bis 2027-03 prüfen. Künftige Daten bis zur Messung versiegeln.
4. **Phase-B-Implementierungsaudit:** Mehrmonatige Trainings-/Zielgrenzen, 90-Tage-Abdeckung, Prognosezählung, OLS, Bootstrap/HAC und Zeitstempel mit *synthetischen Daten* prüfen.
5. Originaldaten, Codeversionen, Manifest-Hashes und die vollständige Prognoseprozedur vor Messung archivieren. Keine GitHub-Versionierung großer Rohdaten oder Secrets.
6. Falls Datenhistorie/Preissemantik/Provenienz unzureichend ist, Phase C **sperren**. Keine automatische Anpassung des Testfensters.

## 7. Ergebnisinterpretation vorab

- Positiv: *Bedingter zusätzlicher Prognosewert von BTC oberhalb der SOL-Kontrollmerkmale im gewählten Zeitraum*, aber **kein Kausalbeweis** und keine Handelsprofitabilität.
- Negativ: Kein Nachweis von Zusatznutzen **unter dieser Kontrolle und diesem Stichprobendesign**, nicht Widerlegung eines beliebigen BTC-Vorlaufs.
- Offen: gemeinsame Marktschocks können auf dieser Datenbasis nicht identifiziert oder ausgeschlossen werden.

## 8. Referenzliteratur

- Corsi (2009). *A Simple Approximate Long-Memory Model of Realized Volatility*. Journal of Financial Econometrics 7, 174–196. DOI: `10.1093/jjfinec/nbp001`.
- Giacomini & White (2006). *Tests of Conditional Predictive Ability*. Econometrica 74, 1545–1578. DOI: `10.1111/j.1468-0262.2006.00718.x`.
- Diebold & Yilmaz (2012). *Better to Give than to Receive: Predictive Directional Measurement of Volatility Spillovers*. International Journal of Forecasting 28, 57–66. DOI: `10.1016/j.ijforecast.2011.02.006`.

**Dieses Dokument ist ein Planungsentwurf, kein bestandener Methodenaudit und keine Freigabe zur Ergebnismessung.**
