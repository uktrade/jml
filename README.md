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

## Update requirements files

`make all-requirements`

## Project documentation
- [Index](docs/index.md)
    - [Environment Variables](docs/environment-variables.md)
    - [Emails](docs/emails.md)
    - [UK SBS](docs/uksbs.md)