# Joiners Movers Leavers prototype

## Setup

- Copy the example env file `cp .env.example .env`
- Copy the example local settings file `cp config/settings/local.example.py config/settings/local.py`
    - Configure env vars (talk to SRE for values)
- Install FE dependancies
    - `npm install` 
- Build local docker instance:
    - `make build`
    - `make migrate` or `make first-use` 
- Start the local docker instance `make up`

## Update requirements files

`make all-requirements`

## Using SSO locally

Uncomment the following value in your `config/settings/local.py`.

```python
AUTHBROKER_ANONYMOUS_PATHS = [
    "/admin/",
    "/admin/login/",
]
```

Comment out the following values in your `config/settings/local.py`.

```python
INSTALLED_APPS += [  # type: ignore
    "dev_tools.apps.DevToolsConfig",
]

LOGIN_URL = reverse_lazy("dev_tools:index")

MIDDLEWARE.append("dev_tools.middleware.DevToolsLoginRequiredMiddleware")  # type: ignore
AUTHENTICATION_BACKENDS.remove("user.backends.CustomAuthbrokerBackend")  # type: ignore
MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")  # type: ignore
```
