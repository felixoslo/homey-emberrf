# EmberRF 0.4.4 – forskjeller fra Maxitrol og dokumentert teststatus

**Dato:** 19. november 2026  
**Formål:** Underlag for vurdering og innsending til Homey App Store.  
**Utgangspunkt:** [Maxitrol for Homey av Michael Dove](https://github.com/michaeldove/homey-maxitrol-fireplace), MIT-lisens, og [Homey App Store-oppføring](https://homey.app/en-nl/app/com.maxitrol.fireplace/Maxitrol/). EmberRF er en selvstendig videreutvikling som viderefører korrekt opphavskreditering.

## Funksjonell sammenligning

| Funksjon | Maxitrol (Michael Dove, v0.1.1) | EmberRF 0.4.4 |
|---|---|---|
| Tenning og slukking | Ja | Ja, fysisk bekreftet på testpeis |
| Flamme opp/ned | Ja, egne knapper og Flow-kort med valgfri varighet | Ja, 50 RF-repetisjoner per knappetrykk; fysisk bekreftet tre trykk fra maksimum til minimum og tre tilbake. Flow-faktor 1–10 |
| Smal og bred brenner/flamme | Ikke eksponert som egne funksjoner | To egne knapper og Flow-handlinger; fysisk bekreftet begge veier |
| RF-signalprofiler | Én standard G6R-profil | Separate standard- og AUX-profiler med forskjellig sluttpuls, nødvendig fordi tenning og bred flamme har samme databiter |
| Dedikerte Flow-handlinger | Flamme opp/ned; standard På/Av | Seks eksplisitte handlinger: På, Av, Bred, Smal, Flamme opp og Flamme ned, samt standard På/Av |
| Flow-utløsere og diagnostikk | Ikke egne RF-resultatutløsere i publisert kildekode | To utløsere for RF akseptert/feil; detaljert teknisk logg. Ingen automatisk skriving til tidslinjen; eventuell tidslinjelogg bestemmes av brukerens Flow |
| Antenne | Støtter kompatibel Homey med 433 MHz-radio, inkludert Bridge | Bruker Homeys innebygde Satellite Mode-antennestyring og viser valgt/sist observert Homey Pro eller Bridge i enheten |
| Paring | Lærer fjernkontrollens 18-biters adresse | Læring av 18-biters adresse **eller** manuell heksadesimal adresse ved behov; ny generell innlæring er ikke fysisk validert |
| Språk | Originalkoden tilbyr engelsk | Norsk og engelsk for app, Flow og paringsvindu med relevante feilmeldinger |
| Status i appen | På/Av er siste sendte kommando, ikke fysisk status | På/Av og anmodet flammemodus er kommandoestimater, ikke fysisk status; ingen gass- eller flammefeedback |

**Reell merverdi:** EmberRF utvider først og fremst kontrollflaten med **smal/bred brenner**, korrekte separate RF-profiler, flere dedikerte Flow-handlinger, RF-resultatutløsere og diagnostikk, avlesning av Homeys native antennevalg, manuell paring og norsk brukergrensesnitt. **På/Av, Flamme opp/ned og Flow-varighet fantes allerede i Maxitrol**; disse skal derfor ikke fremstilles som nye oppfinnelser.

## Tidligere kontakt og forsøk på å få funksjonen inn i eksisterende app

Den **15. november 2026** opprettet vi [GitHub-sak #3 – «AUX / secondary burner support for G6R-H4T2»](https://github.com/michaeldove/homey-maxitrol-fireplace/issues/3) i Michael Doves Maxitrol-prosjekt. Vi ba om støtte for sekundærbrenner/AUX, altså smal og bred flamme, både som direkte Homey-kontroll og som Flow-handlinger. Vi tilbød oss samtidig å hjelpe med testing og ytterligere tekniske opplysninger.

Ved kontroll **19. november 2026** var saken fortsatt **åpen og hadde 0 kommentarer**. Vi har ikke mottatt noe svar fra utvikleren. Dette viser at vi har tatt initiativ til samarbeid før en separat innsending, **men den korte tiden uten svar må ikke fremstilles som at utvikleren har avslått, eller at samarbeid er umulig**. Vi fortsetter derfor å kreditere opphavet og holder døren åpen for samarbeid.

## Dokumentert testing på én G6R-H4T2-installasjon

- **Fysisk bekreftet 19. november 2026 med brukeren ved peisen:** tenning, slukking, veksling mellom smal og bred flamme og regulering opp/ned.
- **Reguleringsresultat:** Tre vanlige «Flamme ned»-trykk ga full senkning, og tre «Flamme opp»-trykk ga full økning. Eksisterende 50 RF-repetisjoner per trykk beholdt.
- **Antenne:** Homeys innebygde Pro/Bridge-valg og visning i EmberRF er testet; visningen alene beviser ikke hvilken fysisk antenne som sendte hvert RF-signal.
- **Automatiske tester:** 26 beståtte i v0.4.4. Homey CLI-bygg og `validate` på publiseringsnivå er bestått.
- **Forenkling etter fysisk test:** Eksperimentell hold-widget og tilhørende bakgrunnskode er fjernet i v0.4.4.
- **Egen testinstallasjon:** En allerede paret EmberRF-enhet ble brukt; denne testen verifiserer ikke første gangs pairing hos nye brukere eller kompatibilitet med andre mottakere.

## Avgrensninger og neste kvalitetssjekk

1. Test ny paring av fjernkontrolladresse, både automatisk innlæring og manuell reserve, på faktisk Homey-utstyr.
2. Test flere G6R-varianter/mottakere og begge radioinstallasjoner før utvidede kompatibilitetspåstander. Michael Doves originalapp er testet på andre oppgitte maskinvaremodeller; testresultatene kan ikke overføres automatisk.
3. Utfør installasjon/oppdatering fra publiserbar versjon og kontroller norsk/engelsk grensesnitt i Homey.
4. Bevar MIT-lisens og kreditering av Michael Dove. Forklar utvidet funksjonalitet og modellfokus åpent ved eventuell vurdering av overlapp med eksisterende Maxitrol-app.
5. Fysisk tilstand kan ikke leses tilbake. Appen må ikke brukes som sikkerhetskontroll eller til uovervåket tenning.

**Publiseringsstatus:** Kildekode v0.4.4 er tilgjengelig på [GitHub](https://github.com/felixoslo/homey-emberrf) og består automatiske tester og Homeys tekniske validering. Den ble **sendt inn til sertifisering 19. november 2026 som bygg 1** og er nå i status `in_review`, uten automatisk publisering ved godkjenning. Den er **ikke** sertifisert eller offentlig publisert i Homey App Store. Ytterligere fysisk kompatibilitets- og pairingtesting anbefales før offisiell innsending. Homeys frivillige AI-forhåndsgjennomgang ble ikke kjørt fordi API-nøkkel manglet; dette er ikke det samme som teknisk validering.
