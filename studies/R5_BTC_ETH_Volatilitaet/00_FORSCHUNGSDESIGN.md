# R5: BTC -> ETH Volatilitaetsprognose
Datum: 2026-11-14
Status: PHASE A - ENTWURF, NICHT FREIGEGEBEN

## Forschungsfrage
Verbessert vergangene BTC-Volatilitaet die Prognose
der naechsten 60 Minuten ETH-Volatilitaet gegenueber
einem Modell mit ausschliesslich ETH-Informationen?

## Vermuteter Mechanismus
Marktweite Informationsschocks koennten zuerst
in BTC sichtbar werden und auf ETH uebergehen.
Alternative: Gleichzeitige Reaktion auf gemeinsame
Informationen ohne eigenstaendige BTC-Prognosekraft.

## Hypothesen
H0: Kein inkrementeller OOS-Prognosevorteil.
H1: BTC-Informationen verbessern die ETH-Prognose.

## Daten
Binance USD-M Perpetual BTC/ETH, 5m, UTC.
Bereits auditierte kanonische Daten.
Originaldaten ausschliesslich lesend.
Historische Testdaten NICHT als Blindtest behandeln.

## Prognoseziel
ETH Realized Variance der folgenden 12 Kerzen:
Summe der 12 quadrierten 5m-Logrenditen.
Horizont: 60 Minuten.
Entscheidung nach abgeschlossener Kerze t.
Zielwerte erst nach Ablauf des Horizonts verfuegbar.

## Vorlaeufige Modellfamilie
B0: Vergangene ETH-Volatilitaet.
B1: ETH-HAR-RV.
M1: ETH-HAR-RV plus vergangene BTC-RV.
HAR-Horizonte als Kandidat: 1h, 1d, 7d.
Kein Machine Learning, keine Indikatorsuche.

## Primaerer Vergleich
Inkrementeller OOS-Prognosefehler M1 gegen B1.
Identische Prognosezeitpunkte.
Effektgroesse und Unsicherheitsintervall.
Keine Handelsprofitabilitaetsbehauptung.

## Vor Messung zwingend festzulegen
- Exakte HAR-RV-Formeln und Transformationen
- Primaere Verlustfunktion und Relevanzmass
- Trainings- und Walk-Forward-Grenzen
- Purging bei 12-Kerzen-Zielen
- Abhaengigkeitstaugliche Inferenz
- Behandlung historischer Mehrfachversuche
- Erfolgs-, Unklar- und Abbruchkriterien
- Unabhaengige neue Bestaetigungsdaten

## Stopregel
Keine Ergebnismessung vor Phase-B-Audit.
Keine Parameteraenderung nach Ergebnisbetrachtung.
Keine produktiven Aenderungen.
