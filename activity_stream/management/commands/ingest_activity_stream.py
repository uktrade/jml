from django.core.management.base import BaseCommand

from activity_stream.utils import ingest_staff_sso_s3


class Command(BaseCommand):
    help = "Ingest Staff SSO Activity Stream"

    def handle(self, *args, **options):
        ingest_staff_sso_s3()
