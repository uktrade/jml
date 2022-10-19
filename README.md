# Joiners, Movers and Leavers Service

## Setup

- Copy the example env file `cp .env.example .env`
- Copy the example local settings file `cp config/settings/local.example.py config/settings/local.py`
    - Configure env vars (talk to SRE for values)
- Install FE dependencies
    - `npm install` 
- Build local docker instance:
    - `make build`
    - `make migrate` or `make first-use` 
- Start the local docker instance `make up`
- Open a browser at `http://localhost:8001/dev-tools/`
- Use the "Change user" form to select a user to impersonate
- Navigate to `http://localhost:8001/leavers/`

## Update requirements files

`make all-requirements`

## Project documentation

- [Index](/docs/index.md)
    - [Environment Variables](/docs/environment-variables.md)
    - [Emails](/docs/emails.md)
    - [UK SBS](/docs/uksbs.md)

## Project structure

- `config/` - Django settings and top-level project config
- `core/` - Common code and integrations with external systems
- `leavers/` - Django app for processing leavers
- `dev_tools/` - Djang app for tooling that helps with development
