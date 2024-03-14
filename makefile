SHELL := /bin/bash
APPLICATION_NAME="Leaving service"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m
COLOUR_RED='\033[0;31m'

.PHONY: help setup

help: # List commands and their descriptions
	@grep -E '^[a-zA-Z0-9_-]+: # .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ": # "; printf "\n\033[93;01m%-30s %-30s\033[0m\n\n", "Command", "Description"}; {split($$1,a,":"); printf "\033[96m%-30s\033[0m \033[92m%s\033[0m\n", a[1], $$2}'

build: # Run docker-compose build
	docker compose build

npm-build: # Install and build npm packages
	npm install
	npm run build

up: # Start the project
	docker compose up

up-detached: # Start the project in a detached state
	docker compose up -d

down: # Stop the project
	docker compose down

# Run a command in a new container
run = docker compose run --rm

# Run a command in a new container without starting linked services
run-no-deps = $(run) --no-deps

# Run a command in an existing container
exec = docker compose exec

# Run on existing container if available otherwise a new one
leavers := ${if $(shell docker ps -q -f name=leavers),$(exec) leavers,$(run) leavers}
db := ${if $(shell docker ps -q -f name=db),$(exec) db,$(run) db}

manage = python manage.py

# Run poetry if it is installed, otherwise run it in the leavers container
POETRY := $(shell command -v poetry 2> /dev/null)
ifdef POETRY
    poetry = poetry --quiet
else
    poetry = $(leavers) poetry --quiet
endif

setup: # Set up the project from scratch
	cp .env.example .env
	cp config/settings/local.example.py config/settings/local.py
	npm install
	npm run build
	docker compose down
	docker compose up -d db opensearch
	$(leavers) $(manage) createcachetable
	$(leavers) $(manage) migrate
	$(leavers) $(manage) collectstatic --no-input
	$(leavers) $(manage) initialise_staff_index
	$(leavers) $(manage) create_test_users
	$(leavers) $(manage) seed_employee_ids
	$(leavers) $(manage) update_staff_index
	$(leavers) $(manage) set_permissions
	$(leavers) $(manage) create_test_users
	docker compose up

check-fixme:
	! git --no-pager grep -rni fixme -- ':!./makefile' ':!./.circleci/config.yml' ':!./.github/workflows/ci.yml'

migrate: # Run migrations
	$(leavers) $(manage) migrate

migrations: # Create needed migrations
	$(leavers) $(manage) makemigrations

empty-migration: # Create an empty migration `make empty-migration app=app_name name=migration_name`
	$(leavers) $(manage) makemigrations $(app) --empty --name=$(name)

checkmigrations: # Check for missing migrations
	$(run-no-deps) leavers $(manage) makemigrations --check

compilescss: # Compile SCSS into CSS
	npm run css:build

shell: # Run a Django shell
	$(leavers) $(manage) shell_plus

flake8: # Run flake8
	$(poetry) run flake8 $(file)

black: # Run black
	$(poetry) run black .

check-black: # Run check-black
	$(poetry) run black . --check

isort: # Run isort
	$(poetry) run isort .

check-isort: # Run check-isort
	$(poetry) run isort . --check

djlint: # Run djlint
	$(poetry) run djlint . --reformat --format-css --format-js

check-djlint: # Run check-djlint
	$(poetry) run djlint . --check

check: # Run formatters to see if there are any errors
	make flake8
	make check-black
	make check-isort
	make check-djlint

fix: # Run formatters to fix any issues that can be fixed automatically 
	make flake8 
	make black 
	make isort 
	make djlint

mypy: # Run mypy
	$(leavers) mypy .

collectstatic: # Run Django collectstatic
	$(leavers) $(manage) collectstatic

bash: # Start a bash session on the application container
	$(leavers) bash

all-requirements: # Generate pip requirements files
	$(poetry) export -f requirements.txt --output requirements.txt --without-hashes --with production --without dev,testing

pytest:
	$(leavers) pytest --cov --cov-report html -raP --capture=sys -n 4

test: # Run tests
	$(leavers) pytest --disable-warnings --reuse-db $(test)

test-fresh: # Run tests with a fresh database
	$(leavers) pytest --disable-warnings --create-db --reuse-db $(test)

view-coverage:
	python -m webbrowser -t htmlcov/index.html

superuser: # Create a superuser
	$(leavers) $(manage) createsuperuser

test-users:
	$(leavers) $(manage) create_test_users

seed-employee-ids:
	$(leavers) $(manage) seed_employee_ids

model-graphs: # Generate model graphs at jml_data_model.png
	$(leavers) $(manage) graph_models -a -g -o jml_data_model.png

ingest-activity-stream:
	$(leavers) $(manage) ingest_activity_stream --limit=10

serve-docs: # Serve mkdocs
	$(poetry) run mkdocs serve -a localhost:8000

staff-index:
	$(leavers) $(manage) ingest_staff_data --skip-ingest-staff-records --skip-service-now

detect-secrets-init: # Initialise the detect-secrets for the project
	$(poetry) run detect-secrets scan > .secrets.baseline

detect-secrets-scan: # detect-secrets scan for the project
	$(poetry) run detect-secrets scan --baseline .secrets.baseline

detect-secrets-audit: # detect-secrets audit for the project
	$(poetry) run detect-secrets audit --baseline .secrets.baseline

poetry-update:
	$(poetry) update

# DB
db-shell: # Open the database container postgres shell
	$(db) psql -U postgres

db-reset: # Reset the database
	docker-compose stop db
	docker-compose rm -f db
	docker-compose up -d db

DUMP_NAME = local

db-dump: # Dump the current database, use `DUMP_NAME` to change the name of the dump
	@PGPASSWORD='postgres' pg_dump postgres -U postgres -h localhost -p 5433 -O -x -c -f ./.dumps/$(DUMP_NAME).dump

db-from-dump: # Load a dumped database, use `DUMP_NAME` to change the name of the dump
	@PGPASSWORD='postgres' psql -h localhost -U postgres postgres -p 5433 -f ./.dumps/$(DUMP_NAME).dump
