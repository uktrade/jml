SHELL := /bin/bash
APPLICATION_NAME="Leaving service"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m
COLOUR_RED='\033[0;31m'

.PHONY: help

help: # Help command
	@grep -E '^[a-zA-Z_-]+:.*?# .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?# "; printf "\033[1;33m%-30s %-30s\033[0m\n", "Command", "Description"}; {split($$1,a,":"); printf "\033[36m%-30s\033[0m \033[32m%s\033[0m\n", a[1], $$2}'

build: # Run docker-compose build
	docker-compose build
	npm install
	npm run build

up: # Run docker-compose up
	docker-compose up

up-detached: # # Run docker-compose up in a detached state
	docker-compose up -d

down: # Run docker-compose down
	docker-compose down

run = docker-compose run --rm
manage = python manage.py
poetry = $(run) leavers poetry --quiet

first-use:
	npm install
	npm run build
	docker-compose down
	docker-compose up -d db opensearch
	$(run) leavers python manage.py createcachetable
	$(run) leavers python manage.py migrate
	$(run) leavers python manage.py collectstatic --no-input
	$(run) leavers python manage.py initialise_staff_index
	$(run) leavers python manage.py create_test_users
	$(run) leavers python manage.py seed_employee_ids
	$(run) leavers python manage.py update_staff_index
	$(run) leavers python manage.py set_permissions
	$(run) leavers python manage.py create_test_users
	docker-compose up

check-fixme:
	! git --no-pager grep -rni fixme -- ':!./makefile' ':!./.circleci/config.yml' ':!./.github/workflows/ci.yml'

migrate: # Run Django migrate
	$(run) leavers python manage.py migrate

migrations: # Run Django makemigrations
	$(run) leavers python manage.py makemigrations

empty-migration: # Create an empty migration `make empty-migration app=app_name name=migration_name`
	$(run) leavers python manage.py makemigrations $(app) --empty --name=$(name)

checkmigrations: # Check for missing migrations
	$(run) --no-deps leavers python manage.py makemigrations --check

compilescss: # Compile SCSS into CSS
	npm run css:build

shell: # Run a Django shell
	$(run) leavers python manage.py shell

flake8: # Run flake8
	$(run) leavers flake8 $(file)

black: # Run black
	$(run) leavers black .

isort: # Run isort
	$(run) leavers isort .

djlint: # Run djlint
	$(run) leavers djlint . --reformat --format-css --format-js

format: flake8 black isort djlint

mypy: # Run mypy
	$(run) leavers mypy .

collectstatic: # Run Django collectstatic
	$(run) leavers python manage.py collectstatic

bash: # Start a bash session on the application container
	$(run) leavers bash

all-requirements: # Generate pip requirements files
	$(poetry) export -f requirements.txt --output requirements.txt --without-hashes --with production --without dev,testing

pytest:
	$(run) leavers pytest --cov --cov-report html -raP --capture=sys -n 4

test: # Run tests
	$(run) leavers pytest --disable-warnings --reuse-db $(test)

test-fresh: # Run tests with a fresh database
	$(run) leavers pytest --disable-warnings --create-db --reuse-db $(test)

view-coverage:
	python -m webbrowser -t htmlcov/index.html

superuser: # Create a superuser
	$(run) leavers python manage.py createsuperuser

test-users:
	$(run) leavers python manage.py create_test_users

seed-employee-ids:
	$(run) leavers python manage.py seed_employee_ids

model-graphs: # Generate model graphs at jml_data_model.png
	$(run) leavers python manage.py graph_models -a -g -o jml_data_model.png

ingest-activity-stream:
	$(run) leavers python manage.py ingest_activity_stream --limit=10

serve-docs: # Serve mkdocs
	poetry run mkdocs serve -a localhost:8001

staff-index:
	$(run) leavers $(manage) ingest_staff_data --skip-ingest-staff-records --skip-service-now

detect-secrets-init: # Initialise the detect-secrets for the project
	$(poetry) run detect-secrets scan > .secrets.baseline

detect-secrets-scan: # detect-secrets scan for the project
	$(poetry) run detect-secrets scan --baseline .secrets.baseline

detect-secrets-audit: # detect-secrets audit for the project
	$(poetry) run detect-secrets audit --baseline .secrets.baseline

poetry-update:
	$(poetry) update
