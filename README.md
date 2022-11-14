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

## Project documentation

Our project documentation is in the `docs` folder. It is written in Markdown and is compiled into HTML using MkDocs.

https://uktrade.github.io/jml

### Running MkDocs locally

MkDocs can be run locally using the `make serve-docs` command which runs the `docs`
docker container. Alternatively, you can run the `docs` docker container by enabling the
`docs` compose profile.

The documentation will be served at `http://0.0.0.0:8002`.
