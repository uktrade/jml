from django.core.management.base import BaseCommand

from activity_stream.utils import ingest_activity_stream


class Command(BaseCommand):
    help = "Ingest Staff SSO Activity Stream"

    def handle(self, *args, **options):
        ingest_activity_stream()
