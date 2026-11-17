# EmberRF – Homey-styring av gasspeis

**EmberRF er en offentlig alfa-app for direkte 433,92 MHz-styring av Maxitrol G6R-H4T2-fjernkontroll og kompatible GV60-gasspeiser fra Homey Pro eller Homey Bridge.** Home Assistant og Broadlink er ikke nødvendige for sending fra appen.

**Alle seks RF-kommandoene er allerede programmert inn.** Man trenger bare å pare den originale G6R-H4T2-fjernkontrollens 18-biters adresse, akkurat som i utgangsappen. Ingen individuell innlæring av På, Av, Bred, Smal, Flamme opp eller Flamme ned. Vi har ennå ikke testet andre peismodeller og påstår ikke at appen virker på dem.

Appen har vanlig **På/Av-bryter**, og egne knapper for **Bred flamme**, **Smal flamme**, **Flamme opp** og **Flamme ned**. På/Av er kun sist bestilte handling, ikke en bekreftelse på om gasspeisen virkelig er av eller på. De seks Flow-handlingene kan sende kommandoer gjentatte ganger; to Flow-utløsere rapporterer akseptert sending eller feil. Apploggen merker hendelser med `EMBERRF TX START`, `TX OK`, `TX FEIL` og `ANTENNE`.

## Installasjon og paring

1. Klon koden og installer Homey CLI. Kjør `python3 -m unittest discover -s tests -q` og `homey app validate --path .`.
2. Installer med `homey app install --path .` på en støttet Homey Pro.
3. Legg til enheten «EmberRF peis». Lær inn **kun adressen** fra G6R-H4T2-fjernkontrollen ved RF-lytting (prøv Flamme ned i omtrent to sekunder), eller oppgi adressen manuelt som heksadesimal 18-biters adresse. **Den nye generelle innlæringen er foreløpig ikke fysisk verifisert.**
4. Velg **Homey Pro** eller **Homey Bridge** under *Innstillinger → Satellite Mode → Antenne*.
5. Test På, Bred, Smal, Flamme opp, Flamme ned og Av én om gangen mens du er ved peisen. Behold originalfjernkontrollen.

## Hvorfor fungerer både tenning og bred flamme?

Begge bruker samme 22-biters RF-datainnhold, men har **ulik avslutningspuls**: omtrent 690 µs for tenning og 361 µs for bred flamme. Smal flamme bruker en annen kommandokode og kort avslutningspuls. Dette ble verifisert med opptak fra fungerende Broadlink og originalfjernkontroll. Mer i [RF-dokumentasjonen](docs/rf-protocol.md).

## Sikkerhet og begrensninger

Dette er en **eksperimentell app**, ikke et gassikkerhetssystem eller en offisiell Homey App Store-app. Homey kan bekrefte at et signal ble akseptert for sending, men ikke at gassventilen reagerte. Ingen automatisk bekreftelse på fysisk status. Ikke bruk til uovervåket tenning. Ulike mottakere må testes individuelt.

Lisens: MIT, med opphavskreditering av [Michael Dove](https://github.com/michaeldove/homey-maxitrol-fireplace). [Plan frem mot offisiell app](docs/roadmap.md).

## Flamme opp/ned – funn fra HA og Broadlink

«Flamme ned» ligger i HA sitt Broadlink-kodelager som **RF**. Dekodingen ga G6R-kommando 1110 med lang avslutningspuls, som også stemmer med 88 gyldige RF-rammer fra originalfjernkontrollen. «Flamme opp» ligger der som **IR**, ikke RF. EmberRF bruker derfor i stedet den originale Maxitrol Homey-appens RF-kommando 1101 med lang avslutningspuls. **RF-varianten av Flamme opp er foreløpig ikke fysisk testet med EmberRF.** Begge har egne knapper og Flow-handlinger.


## v0.3.0 alfa: Hold inne og varighetsfaktor

De modellspesifikke RF-kodene fra den originale Maxitrol-appen er beholdt: **Flamme opp = 1101** og **Flamme ned = 1110**. De fire tidligere fungerende På/Av/Bred/Smal-kodene er ikke endret.

Homeys vanlige knapper Flamme opp og Flamme ned gir et enkelttrykk med 10 RF-repetisjoner. De registrerer ikke pålitelig når fingeren slippes, så de er ikke ekte holdeknapper.

For å justere så lenge du holder inne: Legg til **EmberRF – hold flamme** på et Homey-dashboard. Velg EmberRF-peisen i widgetens innstillinger, og hold inne ▲ Flamme opp eller ▼ Flamme ned. Det sendes korte RF-serier kontinuerlig mens fingeren holdes nede. Slipp for å stoppe. Ved bortfall av kontakt stopper Homey etter ca. 1,2 sekunder uten nytt signal, og alle hold avsluttes automatisk etter maksimalt åtte sekunder. En allerede påbegynt RF-serie kan ikke stoppes øyeblikkelig.

I Flow-kortene **Øk flammen** og **Senk flammen** velger du **varighetsfaktor 1–10**. Faktor 1 = 10 repetisjoner, faktor 5 = 50 og faktor 10 = 100. Dette er ikke en prosent for flammehøyden, men en måling av hvor lenge reguleringssignalet gjentas. Begynn med faktor 1 og juster etter observerte resultater. Hverken widgeten eller denne nye Flow-funksjonen er ennå fysisk verifisert.
