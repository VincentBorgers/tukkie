# Tukkie
<p align="center">
  <p align="center">
  <img src="https://raw.githubusercontent.com/VincentBorgers/tukkie/16dd9989ce5d3cd82cf5e58b982a6a15616b47ce/banner-afbeelding" alt="Tukkie banner" width="100%" />
</p>
</p>
Tukkie is een open-source, privacygerichte home intelligence stack voor Nederlandse huishoudens en makers. Het platform draait lokaal, gebruikt uitsluitend gecontroleerde tools voor acties, bewaart data op de eigen infrastructuur en is ontworpen om later door te groeien naar een VPS-deployment of bredere self-hosted omgeving.

De repository bevat geen persoonlijke data, geen vooraf gevulde live device-configuratie en geen verplichte cloudafhankelijkheden. Runtimebestanden, databases, tokens, voice-modellen en lokale caches blijven buiten versiebeheer.

Open-source release: `v1.0.0`  
Publisher: `WebTukker Labs`  
Initial maintainer: `Vincent Borgers`

## Waarom Tukkie

Tukkie is bedoeld voor gebruikers die een lokale AI-laag bovenop hun smart home willen bouwen zonder directe afhankelijkheid van gesloten cloudplatformen. De kernprincipes zijn:

- lokaal eerst
- Nederlands als primaire taal
- tool-first execution, geen ongecontroleerde code-uitvoering
- uitbreidbaar via adapters, tools en configuratie
- bruikbaar voor zowel desktop als smart display dashboards

## Kernfuncties

- Nederlandse chatinterface met lokale context en geheugenlagen
- Langetermijngeheugen, conversation memory en profielkennis
- Veilige tool execution met bevestiging voor kritieke acties
- Integratietemplates voor Tuya, Ring, Imou en netwerkobservatie
- Offline spraakarchitectuur met Vosk en Piper
- Dashboard voor status, apparaten, camera's, netwerk, energie en suggesties
- YAML-gedreven runtimeconfiguratie voor ruimtes, apparaten, scènes en automatiseringen
- Lokale database-opslag via SQLite, met Chroma-ready vectorlaag
- Voorbereid op uitbreiding richting VPS, extra adapters en voice transports

## Monorepo-structuur

- `server/` FastAPI API, runtime en beveiliging
- `dashboard/` React + Tailwind gebruikersinterface
- `ai-core/` redeneerlaag, leerlogica en LLM-orkestratie
- `memory/` conversation storage, long-term memory en vector abstractie
- `tools/` veilige tool registry en uitvoerlaag
- `integrations/` device adapters en netwerkobservatie
- `config/` instellingen, voorbeeldconfiguraties, prompts en lokale runtimepaden

## Hoe Tukkie werkt

1. De frontend praat met de lokale FastAPI backend.
2. De backend laadt configuratie uit `config/*.yaml`.
3. Berichten gaan door de AI-core, die kennis ophaalt uit memory en device-context.
4. Acties lopen uitsluitend via de toollaag.
5. Device adapters voeren veilige statusvragen en bekende acties uit.
6. Interacties worden opgeslagen zodat routines en automatiseringssuggesties kunnen ontstaan.

## Systeemvereisten

- Windows, Linux of macOS
- Python 3.12+
- Node.js 20+
- npm 10+
- Optioneel: Ollama voor lokale LLM-responses
- Optioneel: Vosk + Piper modellen voor volledige offline spraak

## Snelle start

### 1. Python dependencies installeren

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r server\requirements-voice.txt -r server\requirements-integrations.txt
```

Optioneel voor Chroma:

```powershell
.\.venv\Scripts\python.exe -m pip install -r server\requirements-vector.txt
```

### 2. Dashboard dependencies installeren

```powershell
Set-Location dashboard
npm install
Set-Location ..
```

### 3. Omgevingsbestand klaarzetten

```powershell
Copy-Item .env.example .env
```

Pas daarna de relevante waarden in `.env` aan, zoals databasepad, modelpaden, Ring-credentials of API-hosts.

### 4. Configuratie invullen

De runtimebestanden zijn standaard schoon en leeg. Bewerk deze bestanden met je eigen omgeving:

- `config/assistant.yaml`
- `config/profile.yaml`
- `config/rooms.yaml`
- `config/devices.yaml`
- `config/scenes.yaml`
- `config/automations.yaml`

Voor starttemplates zijn er voorbeeldbestanden beschikbaar:

- `config/assistant.example.yaml`
- `config/profile.example.yaml`
- `config/rooms.example.yaml`
- `config/devices.example.yaml`
- `config/scenes.example.yaml`
- `config/automations.example.yaml`

### 5. Tukkie starten

Backend:

```powershell
.\start_server.ps1
```

Dashboard development server:

```powershell
.\start_dashboard.ps1
```

Na een frontend build serveert FastAPI het dashboard ook rechtstreeks via:

- `http://localhost:8000/`

Development endpoints:

- `http://localhost:5173/`
- `http://localhost:8000/api/overview`
- `http://localhost:8000/health`

## Configuratiemodel

### `config/assistant.yaml`

Definieert productnaam, taal, privacy-instelling, safety en voice-wake word.

### `config/profile.yaml`

Definieert taal, timezone en voorkeuren van de gebruiker of woning.

### `config/rooms.yaml`

Bevat ruimtes, doelen en eventuele metriek per ruimte.

### `config/devices.yaml`

Bevat apparaatdefinities, capabilities, vendor metadata en statusdefaults.

### `config/scenes.yaml`

Bevat bekende scènes die door tools kunnen worden geactiveerd.

### `config/automations.yaml`

Bevat declaratieve regels die de runtime kan tonen, voorstellen of later uitbreiden.

## Voice en lokale AI

Tukkie ondersteunt een lokale voice pipeline zonder verplichte cloudservices.

- Speech-to-text: `Vosk`
- Text-to-speech: `Piper`
- Lokale LLM-ondersteuning: `Ollama`

Installatiescripts:

- `install_vosk_nl_model.ps1`
- `install_piper_nl_voice.ps1`

Gedownloade modellen worden bewust niet meegecommit. Plaats ze onder `config/models/` en stel de paden in via `.env`.

## Integraties

### Tuya

Vul `device_key`, `local_key`, `address` en device metadata in voor lokale LAN-control via `tinytuya`.

### Ring

De Ring-adapter is voorbereid voor status- en intercom/doorbell-scenario's, maar vereist vendor-credentials en tokenbeheer.

### Imou

Ondersteunt lokale snapshot-proxying via `snapshot_url`, optionele `stream_url` en basic authentication.

### Netwerk

De netwerkmodule is read-only en bedoeld voor device-detectie, trafficstatistieken en anomaly summarization.

## Uitbreiden

Tukkie is modulair opgezet. Nieuwe functionaliteit voeg je toe via:

- nieuwe tools in `tools/src/`
- nieuwe integratie-adapters in `integrations/src/`
- extra geheugenlogica in `memory/src/`
- dashboardpanelen in `dashboard/src/components/`

Uitgebreide richtlijnen staan in `docs/extensions.md`.

## Privacy en beveiliging

- Geen directe uitvoering van onbekende of gegenereerde code
- Bevestigingslaag voor kritieke toolacties
- Lokale opslag van profiel-, apparaat- en interactiedata
- Modellen en secrets buiten versiebeheer
- Scheiding tussen AI-besluitvorming en daadwerkelijke device actions

## Deployments

Tukkie draait lokaal als primaire modus, maar is voorbereid op verdere deployment.

- `docker-compose.yml` levert een lokale multi-service workflow
- SQLite is standaard actief
- De memory-architectuur laat toekomstige PostgreSQL-migratie toe
- FastAPI kan het gebuilde dashboard serveren voor single-host VPS deployments

## Open Source Governance

- Licentie: Apache License 2.0
- Security policy: zie `SECURITY.md`
- Contributing guide: zie `CONTRIBUTING.md`
- Gedragsregels: zie `CODE_OF_CONDUCT.md`
- Release notes: zie `docs/releases/v1.0.0.md`
- Auteurs en onderhoud: zie `AUTHORS.md`

## Release v1.0.0

De eerste open-source release zet Tukkie neer als configureerbare, Nederlandstalige en lokaal georiënteerde basis voor een zelfstandige home intelligence omgeving. Deze release richt zich op architectuur, privacy, uitbreidbaarheid en een direct bruikbare developer- en gebruikerservaring.
