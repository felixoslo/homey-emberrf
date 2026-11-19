# Utkast til innsending: EmberRF 0.4.4

**Status:** Forberedt utkast – ikke sendt til Homey App Store.

## Søknadstekst til Homeys vurdering (norsk)

EmberRF er en uavhengig, MIT-lisensiert videreutvikling av Michael Doves Maxitrol-app for styring av kompatible G6R-H4T2-gasspeiser over 433,92 MHz. Appen tilbyr den vanlige tenning/slukking- og flamme opp/ned-styringen, men utvider funksjonaliteten vesentlig med **egen styring av sekundærbrenneren (AUX), altså bred og smal flamme**. Dette er tilgjengelig fra Homey-enheten og egne Flow-handlinger. To forskjellige RF-signalprofiler brukes for hovedkontroll og AUX; egne Flow-resultatutløsere, teknisk diagnostikk, Homeys innebygde antennevalg og norsk/engelsk grensesnitt følger med.

Vi forsøkte først å få den viktigste tilleggsfunksjonen inn i eksisterende app ved å åpne [GitHub-sak #3 hos Michael Dove 15. november 2026](https://github.com/michaeldove/homey-maxitrol-fireplace/issues/3). Forslaget gjaldt AUX/sekundærbrenner både i appen og via Flows, og tilbød assistanse til testing. **Per 19. november 2026 er saken åpen uten kommentarer, og vi har ikke mottatt svar**. Det korte tidsrommet uten svar er ikke ment som påstand om avslag fra opprinnelig utvikler; videre samarbeid er fortsatt ønskelig.

Alle seks RF-kommandoer – På, Av, Bred, Smal, Flamme opp og Flamme ned – er fysisk bekreftet på én G6R-H4T2-installasjon 19. november 2026. Regulering fungerer med omtrent tre trykk i hver retning mellom ytterpunktene. De 26 automatiske testene og Homeys tekniske publiseringsvalidering består. Den tidligere eksperimentelle holdewidgeten er fjernet etter brukertesting.

Vi gjør ikke krav på bred kompatibilitet før den er testet; særlig ny paring og flere håndsett/mottakere bør verifiseres. RF er enveis: Appen kan ikke bekrefte fysisk gass- eller flammestatus. Produsentens sikkerhetsfunksjoner beholdes, og uovervåket tenning anbefales ikke. Michael Doves bidrag krediteres tydelig under MIT-lisensen.

## Før faktisk innsending

- Verifiser installasjon/paring fra ny bruker, både innlæring og manuell adresse, og eventuelle oppdateringsforløp.
- Se gjennom tilgjengelige Homey-kompatibilitetspåstander og norske/engelske skjermer.
- Kontroller App Store-oppføringen og eventuelle krav til utviklerkonto/testversjon.
- Få eksplisitt bekreftelse før innsending til Homey; dette dokumentet er kun et utkast.
