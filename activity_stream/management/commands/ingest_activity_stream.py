from django.core.management.base import BaseCommand

from activity_stream.utils import ingest_activity_stream


class Command(BaseCommand):
    help = "Ingest Staff SSO Activity Stream"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, nargs="?")

    def handle(self, *args, **options):
        limit = options["limit"]
        ingest_activity_stream(limit)
