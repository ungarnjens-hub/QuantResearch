# R4 Statistik-Ergänzung
Datum: 2026-11-14
Status: Phase B, vor Ergebnismessung

## Primärer Vergleich
Identische OOS-Prognosezeitpunkte für B1 und M1.
d_t = Fehler(B1)^2 - Fehler(M1)^2.
Delta = Mittelwert(d_t).
Relative Verbesserung =
100 * Delta / MSE(B1).

## Bootstrap
Methode: Moving-Block-Bootstrap auf Kalenderwochen.
Wochen: Montag 00:00 UTC bis Montag 00:00 UTC.
Unvollständige Randwochen bleiben enthalten.
Jede Woche enthält ihre chronologisch geordneten
gepaarten B1/M1-Prognosefehler.

Blocklänge: 4 aufeinanderfolgende Wochen.
Sampling: zufällige Startwochen mit Zurücklegen.
Nur tatsächlich aufeinanderfolgende Wochen.
Blöcke aneinanderfügen, bis mindestens so viele
Wochen wie im Original vorliegen; danach auf
die ursprüngliche Wochenanzahl abschneiden.

Replikation: Wochenblöcke zusammenfügen und
MSE beider Modelle aus allen enthaltenen
Einzelprognosen neu berechnen.
Keine Mittelung ungewichteter Wochen-MSEs.
Wiederholungen: 2000.
Seed: 20261114.
Intervall: empirische Perzentile 2.5% und 97.5%.
Einzelwochen-Bootstrap aus V2/V3 wird durch
diese vor Messung fixierte Spezifikation ersetzt.

## Sekundäre Prüfung
Clark-West-adjustierte Verlustdifferenz:
cw_t = e_B1^2 - e_M1^2 + (f_B1 - f_M1)^2.
Einseitige Prüfung positiver CW-Mitteldifferenz.
HAC-Lag 12, Intercept-only Regression.
Voraussetzungen und Grenzen dokumentieren.
CW ersetzt weder tatsächliche MSE-Wirkung
noch die unabhängige Bestätigung.

## Zeitliche Korrektheit
Features aus vollständig abgeschlossener Kerze t.
Ziel: ETH-Close(t) bis ETH-Close(t+1).
Trainingslabel muss zum Trainingsstichtag
vollständig bekannt sein.
Keine Verwendung späterer Daten beim Fit.
Monatliche Modelle nur auf früheren Labels.
Keine Prognosen bei fehlender Synchronisation.

## Bewertung
Primär: Effektgröße und Bootstrap-Intervall.
Explorative Evidenz nur, falls die Untergrenze
der relativen Verbesserung über null liegt.
CW ist sekundär, nicht alternatives Erfolgstor.
Blocklänge nicht anhand der Ergebnisse verändern.
Cross-Week-Abhängigkeit und Nichtstationarität
bleiben methodische Einschränkungen.

Kein Blindtest, keine Profitabilitätsbehauptung.
Keine nachträgliche Parametersuche.
