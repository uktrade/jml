"""Fetch staff data from multiple sources and store it.

This command is how we get staff data into the application.

Usage:
    # Ingest from all data sources with no limits.
    python manage.py ingest_staff_data

    # Apply limits and skip some data sources.
    python manage.py ingest_staff_data \
        --limit-people-finder=100 \
        --skip-ingest-staff-records \
        --skip-service-now \
        --skip-index-sso-users \
        --skip-people-finder
"""

import time
from typing import Callable

from django.core.management.base import BaseCommand

from core.tasks import (
    index_sso_users_task,
    ingest_activity_stream_task,
    ingest_people_data_task,
    ingest_people_finder_task,
    ingest_service_now_task,
)


class Command(BaseCommand):
    help = "Command template"

    def add_arguments(self, parser):
        parser.add_argument("--limit-people-finder", type=int, default=None)
        parser.add_argument("--skip-ingest-staff-records", action="store_true")
        parser.add_argument("--skip-index-staff-records", action="store_true")
        parser.add_argument("--skip-people-finder", action="store_true")
        parser.add_argument("--skip-service-now", action="store_true")

    def handle(self, *args, **options) -> None:
        if not options["skip_ingest_staff_records"]:
            self._run_task(
                "ingest_staff_records",
                ingest_activity_stream_task,
            )

        if not options["skip_index_staff_records"]:
            self._run_task("index_staff_records", index_sso_users_task)

        if not options["skip_people_finder"]:
            self._run_task(
                "ingest_people_finder",
                ingest_people_finder_task,
                limit=options["limit_people_finder"],
            )

        # TODO: Add a condition on the service now enabled setting.
        if not options["skip_service_now"]:
            self._run_task("ingest_service_now", ingest_service_now_task)

        self._run_task("ingest_people_data", ingest_people_data_task)

    def _run_task(self, task_name: str, task: Callable, *args, **kwargs) -> None:
        self.stdout.write(self.style.WARNING(f"Starting task {task_name}"))
        t0 = time.perf_counter()
        task(*args, **kwargs)
        t1 = time.perf_counter()
        self.stdout.write(
            self.style.SUCCESS(f"Finished task {task_name} in {t1 - t0:0.4f} seconds")
        )
