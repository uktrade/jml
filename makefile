SHELL := /bin/bash
APPLICATION_NAME="Financial Forecast Tool"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m
COLOUR_RED='\033[0;31m'

.PHONY: help test
help:
	@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) ---|$(COLOUR_NONE)"
	@echo -e "$(COLOUR_YELLOW)make build$(COLOUR_NONE) : Run docker-compose build"
	@echo -e "$(COLOUR_YELLOW)make up$(COLOUR_NONE) : Run docker-compose up"
	@echo -e "$(COLOUR_YELLOW)make down$(COLOUR_NONE) : Run docker-compose down"
	@echo -e "$(COLOUR_YELLOW)make migrations$(COLOUR_NONE) : Run Django makemigrations"
	@echo -e "$(COLOUR_YELLOW)make migrate$(COLOUR_NONE) : Run Django migrate"
	@echo -e "$(COLOUR_YELLOW)make compilescss$(COLOUR_NONE) : Compile SCSS into CSS"
	@echo -e "$(COLOUR_YELLOW)make shell$(COLOUR_NONE) : Run a Django shell"
	@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Run flake8 checks"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black"
	@echo -e "$(COLOUR_YELLOW)make isort$(COLOUR_NONE) : Run isort"
	@echo -e "$(COLOUR_YELLOW)make collectstatic$(COLOUR_NONE) : Run Django BDD tests"
	@echo -e "$(COLOUR_YELLOW)make bash$(COLOUR_NONE) : Start a bash session on the application container"
	@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate pip requirements files"
	@echo -e "$(COLOUR_YELLOW)make pytest$(COLOUR_NONE) : Run pytest"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black formatter"

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

first-use:
	docker-compose down
	docker-compose up -d db
	docker-compose run --rm leavers python manage.py migrate
	docker-compose run --rm leavers python manage.py create_test_users
	docker-compose up

migrations:
	docker-compose run --rm leavers python manage.py makemigrations

migrate:
	docker-compose run --rm leavers python manage.py migrate

compilescss:
	docker-compose run --rm leavers python manage.py compilescss

shell:
	docker-compose run --rm leavers python manage.py shell

flake8:
	docker-compose run --rm leavers flake8 $(file)

black:
	docker-compose run --rm leavers black .

isort:
	docker-compose run --rm leavers isort .

collectstatic:
	docker-compose run --rm leavers python manage.py collectstatic

bash:
	docker-compose run --rm leavers bash

all-requirements:
	docker-compose run --rm leavers pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm leavers pip-compile --output-file requirements/dev.txt requirements.in/dev.in
	docker-compose run --rm leavers pip-compile --output-file requirements/prod.txt requirements.in/prod.in

pytest:
	docker-compose run --rm leavers pytest -raP --capture=sys --ignore=node_modules --ignore=front_end --ignore=features --ignore=staticfiles -n 4

superuser:
	docker-compose run --rm leavers python manage.py createsuperuser

test-users:
	docker-compose run --rm leavers python manage.py create_test_users
