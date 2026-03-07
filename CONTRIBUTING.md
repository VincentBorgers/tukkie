# Contributing

Bedankt voor je interesse in Tukkie.

## Richtlijnen

- Houd wijzigingen modulair en herleidbaar.
- Behoud de scheiding tussen AI-redenering, tooluitvoering en device-integraties.
- Voeg geen persoonlijke data, secrets, tokens, databases of voice-modellen toe aan commits.
- Nieuwe acties op apparaten moeten via de toollaag lopen, niet direct vanuit de LLM-laag.
- Kritieke acties horen expliciete bevestiging te ondersteunen.

## Werkwijze

1. Fork of clone de repository.
2. Maak een branch per wijziging.
3. Werk documentatie bij als gedrag of configuratie verandert.
4. Draai minimaal de backend compile-check en de dashboard build.
5. Open daarna een pull request met een duidelijke beschrijving van doel, impact en verificatie.

## Verwachte kwaliteit

- Geen ongecontroleerde code-executie toevoegen
- Geen vendor-credentials in voorbeeldconfiguraties opnemen
- Nieuwe integraties moeten een veilige status- en health-implementatie hebben
- Frontendwijzigingen moeten bruikbaar blijven op grote schermen en smart displays

## Contact

Voor projectonderhoud en governance: Vincent Borgers <info@vincentborgers.nl>

