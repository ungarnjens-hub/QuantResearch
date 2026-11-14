# R7 – Methodenaudit (Phase B, Stand 14.11.2026)

**Status: NICHT FREIGEGEBEN zur Marktmessung.**  
**Geltung:** Neue mechanistische Forschungsfrage; R5/R6 und der Zeitraum 01.08.–31.10.2026 bleiben unverändert und verbraucht.

## 1. Ausgangslage und prüfbare Frage
R5/R6 belegen unter Einschränkungen eine inkrementelle Prognoseinformation vergangener BTC-Volatilität für die künftige 60-Minuten-Volatilität von ETH/SOL. Sie belegen weder strukturelle Kausalität noch, ob BTC Ursache oder Proxy eines unbeobachteten gemeinsamen Faktors ist.

Der R7-Entwurf formuliert zwei alternative Erklärungen:
- **A: gerichteter prädiktiver Vorlauf** (BTC-Information vor ETH/SOL).
- **B: gemeinsamer Marktfaktor** (BTC als Proxy für gemeinsamen Schock).

### Kritischer Auditbefund
A und B sind **nicht logisch gegensätzlich** und **nicht allein durch die Gegenrichtung des Prognosevergleichs identifizierbar**. Beide können gleichzeitig gelten. Zeitlich gerichtete Predictability, Granger-Kausalität im Prognosesinn, verallgemeinerte VAR-Varianzzerlegungen und strukturelle Kausalität sind getrennte Konzepte.

## 2. Geeignete Literatur und Methoden
- **Diebold & Yilmaz (2012)**, *International Journal of Forecasting* 28:57–66, DOI: 10.1016/j.ijforecast.2011.02.006. Verallgemeinerte VAR-Varianzzerlegung für gerichtete **prädiktive** Volatilitätsverflechtung; kein Beweis kausaler Schocks.
- **Pesaran & Shin (1998)**, *Economics Letters* 58:17–29, DOI: 10.1016/S0165-1765(97)00214-0. Generalisierte Impulsantworten ohne Variablenordnungsabhängigkeit, aber ohne automatische strukturelle Schockidentifikation.
- **Clark & West (2007)**, *Journal of Econometrics* 138:291–311, DOI: 10.1016/j.jeconom.2006.05.023. Anpassung prädiktiver Fehlerdifferenzen für verschachtelte Modelle.
- **Giacomini & White (2006)**, *Econometrica* 74:1545–1578, DOI: 10.1111/j.1468-0262.2006.00718.x. Vergleich vollständiger Prognoseverfahren inklusive Schätzunsicherheit.

## 3. Harte methodische Probleme vor einer Messung

1. **Zielverwechslung:** Inkrementeller Prognosewert ist nicht gleich kausale Übertragung. R7 darf maximal *gerichtete Prognoseinformation* als Primäraussage beanspruchen.
2. **Gemeinsame Faktoren:** Die umgekehrte Prognoserichtung ist kein zuverlässiger Ersatz für einen gemeinsamen-Faktor-Kontrollvergleich. Benötigt wird ein eigener, vorab definierter Proxy oder Faktoransatz inklusive der Erklärung, welche Information zum Forecast-Zeitpunkt bekannt ist.
3. **Auswahl nach positiver Vorgeschichte:** BTC/ETH/SOL wurden auf Basis von R5/R6 gewählt. Historische Signifikanzen für R7 müssen als explorativ gelten; die Auswahl ist Bestandteil des Versuchsregisters.
4. **Verbrauchte Zeiträume:** Bis einschließlich 31.10.2026 wurde der R5/R6-Mechanismus bereits für Validierung verwendet; ein R7-Test darauf wäre kein unabhängiger Blindtest. Auch ältere historische Abschnitte sind nicht automatisch unverbraucht.
5. **Spezifikation:** Regressanden, RV-Definition, festgelegte Lags, Verfügbarkeitszeitpunkte, Vorhersagehorizont, Modell-/Schätzfenster, Zielmärkte, Kontrollvariablen und *ein* primärer Endpunkt fehlen.
6. **Abhängigkeit/Mehrfachtests:** Die Zahl der Richtungs- und Faktorvergleiche, ihre Fehlerkontrolle sowie HAC-/Blockbootstrap-Basis müssen vor dem ersten Blick auf die R7-Ergebnisse festliegen.
7. **Zeitstempel und News-Latenz:** Gleichzeitige BTC- und ETH/SOL-Kerzen dürfen nicht als vorlaufende Information ausgegeben werden; nur abgeschlossene, zum Entscheidungspunkt verfügbare Beobachtungen.
8. **Erklärungsreichweite:** Selbst bei asymmetrischem Zusatznutzen lassen sich unbeobachtete gemeinsame Schocks nicht ausschließen.

## 4. Empfohlene, eng begrenzte Umsetzung von Phase A (noch keine Messung)

**Ein Primärziel:** Test des *gerichteten inkrementellen* OOS-Prognosebeitrags BTC → ETH/SOL im Unterschied zur Gegenrichtung, mit klar benannten identischen Informationsstichtagen und eigenständigen Eigenhistorien-Baselines. Vollständige Modell- und Lag-Spezifikation erst schriftlich fixieren; kein Versuchsbündel.

**Separates sekundäres Erkenntnisziel:** Sensitivität gegenüber einem vorher festgelegten gemeinsamen Risikofaktor-Proxy prüfen, *nur wenn dessen Datenherkunft und Echtzeitverfügbarkeit belegt sind*. Falls nicht, bleibt die Faktor-/Kausalfrage ausdrücklich **ungeklärt**, statt einen unzureichenden Kontrollvergleich zu erzwingen.

**Auswertung:** Chronologisch vorab festgelegte Trainings- und Testfenster; keine Überlappung unbekannter Labels; gepaarte Verlustdifferenzen; Unsicherheitsintervalle mit dokumentierter Zeitabhängigkeit; Mehrfachtestkorrektur; negative Ergebnisse unverändert berichten.

**Daten:** Zunächst Register und Quellenverfügbarkeit prüfen, ohne neue Ziel- oder Fehlermessungen. Ein bereits verwendeter historischer Zeitraum kann *explorativ* dienen, aber nicht als unverbrauchter Blindtest.

## 5. Go/No-Go für Phase C

**NO-GO bis:**
- primäre Hypothese und Abgrenzung zu R5/R6 konkret falsifizierbar sind;
- alternative gemeinsame-Faktor-Erklärung methodisch fair behandelt oder explizit ausgeklammert ist;
- Daten-/Zeitfenster-Register den Status jedes Abschnitts festhält;
- alle Modell-, Inferenz-, Auswahl- und Abbruchregeln versioniert sind;
- gesonderter Methodenaudit auf konkreten Runner/Informationsfluss mit synthetischen Daten bestanden ist.

**Bis dahin keine R7-Ergebnismessung, kein Backtest, keine Änderungen an TradingLab oder Paper-Bots.**

## 6. Archivhinweis
Dieses Dokument ist ein methodischer Prüfbericht, **keine nachträgliche Vorregistrierung**. Git-Commit vor einer künftigen R7-Messung aufbewahren. Die vorhandenen R5/R6-Archive bleiben eingefroren.
