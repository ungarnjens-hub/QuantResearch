# R7 – Phase B: Synthetische Volatilitäts-Kalibrierung

**Datum:** 14. November 2026  
**Status:** DIAGNOSTISCHER TEST, **KEINE PHASE-C-FREIGABE**  
**Daten:** Ausschließlich künstlich erzeugte 5-Minuten-Renditen für drei Märkte. Kein Zugriff auf Binance, lokale historische Marktdaten oder TradingLab.

## Prüfdesign

Vorab im Skript fixiert: pro Szenario **80** unabhängig simulierte synthetische Datensätze, fortlaufende 5-Minuten-Reihen, persistente stochastische Log-Volatilität, 12/288/2016-Kerzen-HAR-Merkmale, 60-Minuten-ETH-RV-Ziel, monatliche expandierende OLS-Fits, B2 (ETH+SOL) gegen M2 (ETH+SOL+BTC), **2.159** Testprognosen für 90 Tage. Nur zum Prognosezeitpunkt bekannte Merkmale und vor dem Modell-Refit verfügbare Labels. Primäre Differenz: relativer MSE, 95%-Intervall durch gepaarten 7-Tage-Blockbootstrap (5.000 Ziehungen); ergänzend tägliche HAC(7)-Inferenz. Positiv-Gate: Gewinn > 0, Bootstrap-Untergrenze > 0, HAC einseitig p < 0,05.

Szenarien:

1. **Unabhängige BTC-Null:** BTC-Volatilität und BTC-Renditeschocks unabhängig von ETH/SOL; ETH und SOL haben miteinander gemeinsame Schocks. *Eng definierte Prognose-Null, nicht repräsentativ für Krypto im Allgemeinen.*
2. **Gemeinsamer Risikofaktor:** Gemeinsamer persistenter Log-Volatilitätsfaktor und gleichzeitige Renditeschocks; **kein expliziter verzögerter BTC-spezifischer Einfluss** auf die ETH-Volatilität. BTC kann dennoch echte ergänzende Information über den latenten gemeinsamen Faktor liefern. Daher **kein Nullszenario für den bedingten Prognosewert**, sondern eine diagnostische Herausforderung für die kausale Interpretation.
3. **Schwacher struktureller Vorlauf:** Szenario 2 plus festgelegte ETH-Logvol-Ladung von **0,10** auf den um 12 Kerzen verzögerten BTC-idiosynkratischen Volatilitätsfaktor. Die Wirkung in MSE-Prozent wurde **nicht** auf 1–2 % eingestellt.

## Ergebnisse

| Szenario | Positive Gates | Rate | Exaktes 95%-Binomialintervall | Mittlere relative MSE-Verbesserung |
|---|---:|---:|---:|---:|
| Unabhängige BTC-Null | 1/80 | 1,25 % | 0,03–6,77 % | −0,080 % |
| Gemeinsamer Risikofaktor ohne BTC-Vorlauf | 70/80 | 87,50 % | 78,21–93,84 % | +2,403 % |
| Künstlicher BTC-Vorlauf (Ladung 0,10) | 78/80 | 97,50 % | 91,26–99,70 % | +3,695 % |

## Bewertung

**Wichtigster Befund:** Das Verfahren kann bei einem gemeinsamen latenten Faktor häufig zusätzliche BTC-Prognoseinformation finden, **ohne dass ein BTC-spezifischer kausaler Vorlauf konstruiert wurde**. Eine Verbesserung M2 gegenüber B2 ist daher mit der Proxy-Erklärung voll vereinbar. Der Test kann die beiden Ursachen **nicht trennscharf identifizieren**.

Die unabhängige BTC-Null erzeugt nur einen positiven Fall unter 80 Simulationen. Das 95%-Intervall der Fehlalarmrate reicht dennoch bis **6,77 %**; eine nominale Fehlerwahrscheinlichkeit unter 5 % ist damit **nicht nachgewiesen**.

Die künstliche Vorlaufalternative erzielt durchschnittlich +3,70 % MSE-Verbesserung und stellt deshalb **keinen** kontrollierten Test für schwache 1–2%-Effekte dar. Aus den 78/80 positiven Fällen darf keine hohe Teststärke für reale 1–2%-Effekte abgeleitet werden.

Simulationen sind modellabhängig; die realisierte gemeinsame Struktur, Volatilitätsdynamik und Datenprobleme realer Futures-Märkte werden nicht vollständig nachgebildet. Die verwendete HAC-/Bootstrap-Kombination ist deshalb noch nicht allgemein kalibriert.

## Abweichung und Nachverfolgbarkeit

Der vorherige Phase-B-Selbsttest verwendete vereinfachte stündliche Prädiktoren. **Dieser neue Durchlauf** nutzt eine durchgehende synthetische 5-Minuten-Pipeline je Replikation. Ein zunächst gestarteter unoptimierter Prozess wurde nach zwei Szenarien durch die Laufzeitbegrenzung abgebrochen. Der komplette Lauf wurde daraufhin **ohne Änderungen an Seed, DGP-Parametern, Szenarien, Ziehungszahl oder Gate** erneut ausgeführt. Lediglich die numerisch äquivalente AR(1)-Erzeugung wurde von einer Python-Schleife auf `scipy.signal.lfilter` umgestellt. Angegeben werden ausschließlich Werte aus dem **vollständigen** Rechenlauf.

**Keine Untersuchung realer Marktdaten; kein unabhängiger Test von R5/R6 und kein Trading-System-Test.**

## Methodische Konsequenzen / Go-No-Go

- **GO für weiteres Phase-B-Methodendesign** der bedingten BTC-Prognoseinformation.
- **NO-GO für kausale Aussagen** und jede Form der Ergebnisfreigabe auf Marktdaten.
- Vor Phase C: Inferenz für verschachtelte Modelle, überlappende 60-Minuten-Ziele, Label-Verfügbarkeit und Sensitivität von Bootstrap/HAC weiter auditieren; die Fehlerkontrolle anhand zusätzlicher und anders spezifizierter Null-DGPs absichern.
- Wenn Ziel weiterhin die Ursache des BTC-Effekts ist, muss zusätzlich ein identifizierbares Design für gemeinsame Faktoren oder ein ausdrückliches *nicht identifizierbar* im Ergebnisprotokoll festgelegt werden.
- Zukünftige Testperiode Jan–März 2027 **nicht vorzeitig verwenden**. R5/R6-Archive und Paper-Systeme bleiben unverändert.

## Dateien

- `R7_synthetische_kalibrierung_v2.py` (reproduzierbarer Simulationscode)
- `R7_synthetik_realistische_nullkalibrierung_resultat.json` (rechnerische Ausgaben)

**Fazit:** Die neue Simulation widerlegt nicht die Prognosehypothese. Sie zeigt vielmehr, warum ein bedingter BTC-Prognosevorteil noch keine Erklärung seiner Ursache ist. R7 bleibt in Phase B.
