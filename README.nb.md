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

«Flamme ned» ligger i HA sitt Broadlink-kodelager som **RF**. Dekodingen ga G6R-kommando 1110 med lang avslutningspuls, som også stemmer med 88 gyldige RF-rammer fra originalfjernkontrollen. «Flamme opp» ligger der som **IR**, ikke RF. EmberRF bruker derfor i stedet den originale Maxitrol Homey-appens RF-kommando 1101 med lang avslutningspuls. **RF-varianten av Flamme opp er nå fysisk testet på én G6R-H4T2-peis.** Begge har egne knapper og Flow-handlinger.


## Flammejustering med knappetrykk og Flow-faktor

De modellspesifikke RF-kodene fra den originale Maxitrol-appen er beholdt: **Flamme opp = 1101** og **Flamme ned = 1110**. De fire tidligere fungerende På/Av/Bred/Smal-kodene er ikke endret.

Homeys knapper Flamme opp og Flamme ned gir **50 RF-repetisjoner per trykk**. Ved fysisk test ga tre trykk fra maksimal til minimal flammehøyde og tre trykk tilbake. Den eksperimentelle hold-widgeten er derfor fjernet fra versjon 0.4.4.

I Flow-kortene **Øk flammen** og **Senk flammen** velger du **varighetsfaktor 1–10**. Faktor 1 = 10 repetisjoner, faktor 5 = 50 og faktor 10 = 100. Dette er ikke en prosent for flammehøyden, men en måling av hvor lenge reguleringssignalet gjentas. Begynn med faktor 1 og juster etter observerte resultater. Flow-varighetsfaktorene er ikke individuelt kalibrert mot peisens faktiske flammehøyde.

Hver knapp utfører en avgrenset RF-sending. Ingen sending starter automatisk ved oppstart av appen.


## v0.4.0 alfa – lengre flammejustering og loggføring

Ett kort trykk på **Flamme opp** eller **Flamme ned** sender nå **50 RF-repetisjoner som én TX-kommando**, fem ganger lengre enn de tidligere 10. Dette er ikke fem separate klikk. Målet er færre pip og større justering per trykk, men hvor mange av peisens 22 fysiske trinn det gir må testes. I Flow velger man fortsatt faktor 1–10 (10–100 repetisjoner per sammenhengende TX-kall). Hold-widgeten er fjernet i v0.4.4 etter fysisk testing av de vanlige knappene.

Appen har nå en avlesbar tilstand **Flammemodus (anmodet)** med «Smal flamme», «Bred flamme» og «Ukjent», som oppdateres etter en akseptert RF-sending. Det er *ikke* målt fysisk brennerstatus. For en lesbar historikk kan Homey Flow-kortet «RF-kommando ble akseptert av Homey» kobles til tidslinjelogg, som viser blant annet bred/smal flamme og justeringer.

### v0.4.1: Avlesning av antenne

Homeys innebygde antennevalg leses via Python-SDKens `get_settings()` (reserve: `get_setting()`) og ved `on_settings()`. Egen, skrivebeskyttet **Antenne (Homey-innstilling)** viser Homey Pro, Homey Bridge eller «Ikke rapportert av app-SDK». Vi gjetter ikke hvis SDK ikke eksponerer Homeys systeminnstilling. RF sendes fortsatt med `device=self`, slik at Homey selv velger antenne. Lesingen er ikke en fysisk bekreftelse på hvilken sender som bruktes.

### v0.4.3: Verifisert antennevalg

Antennebytte skal gjøres via Homeys innebygde **Enhet → Avanserte innstillinger → Satellite Mode → Antenne**, der Homey Pro og Homey Bridge kan velges. Homey Python-SDK skjuler av og til det reserverte feltet ved appstart, men melder endringer via on_settings(). EmberRF viser derfor siste faktisk observerte Homey-valg som skrivebeskyttet avlesning, også etter appomstart. En forsøksvelger inne i EmberRF ble fjernet da praktisk test viste at den bare endret appvisningen, ikke den ekte Homey-innstillingen. Vi ber ikke om global homey:manager:api-adgang for en peisapp. ChatGPT kan endre og lese det autoritative antennevalget ved behov via den separat autoriserte Homey API-integrasjonen. Ingen RF sendes ved endringer.

### v0.4.4: Forenklet betjening

Den eksperimentelle hold-funksjonen, tilhørende widget og API er fjernet. Vanlige knapper med 50 repetisjoner beholdes uendret. Øvrige RF-kommandoer og antennevalg er ikke endret.

### v0.4.4: Norsk og engelsk paring

Paringsvinduet og vanlige feilmeldinger er oversatt til norsk og engelsk med Homeys språkstøtte. Engelsk brukes som reservespråk for øvrige språk.
