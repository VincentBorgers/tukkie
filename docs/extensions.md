# Extending Tukkie

Tukkie is opgezet als een modulair systeem. Nieuwe functionaliteit hoort op de juiste laag terecht te komen.

## Nieuwe tools

Voeg tools toe in `tools/src/vha_tools/builtins.py` of splits ze uit naar extra modules.

Elke tool hoort te hebben:

- een unieke naam
- een duidelijke beschrijving
- een schema model voor inputvalidatie
- een veilige uitvoerfunctie
- expliciete markering als de actie kritisch is

## Nieuwe integraties

Nieuwe integraties komen in `integrations/src/vha_integrations/`.

Een adapter hoort minimaal te implementeren:

- `health()`
- `get_status(device)`
- `execute_action(device, action, payload)`

Voor camera-achtige bronnen kan ook `fetch_snapshot(device)` worden toegevoegd.

## Nieuwe geheugenlagen

Tukkie gebruikt nu SQLite voor structured memory en een Chroma-ready vectorlaag voor retrieval. Nieuwe geheugenlogica hoort:

- bestaande data niet impliciet te overschrijven
- verklaarbaar te blijven voor de gebruiker
- lokale opslag als standaard te respecteren

## Nieuwe dashboardpanelen

Frontendpanelen leven onder `dashboard/src/components/`. Houd nieuwe panelen:

- duidelijk taakgericht
- geschikt voor brede dashboards
- leesbaar op smart displays
- afhankelijk van bestaande API-routes of expliciet nieuwe routes

## Veiligheidsregel

Laat de AI-laag nooit rechtstreeks systeemcode of onbekende scripts uitvoeren. Tooling en integraties blijven de enige toegestane actielaag.

