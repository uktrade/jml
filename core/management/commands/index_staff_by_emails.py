from django.core.management.base import BaseCommand

from core.utils.staff_index import index_staff_by_emails


class Command(BaseCommand):
    help = "Provide a comma separated list of email addresses you want to index"

    def add_arguments(self, parser):
        parser.add_argument("--emails", type=str, nargs="?")

    def handle(self, *args, **options):
        email_list = str(options["emails"]).split(",")

        self.stdout.write(self.style.WARNING((f"Indexing {email_list}")))

        index_staff_by_emails(email_list)

        self.stdout.write(self.style.SUCCESS(("Job finished successfully")))
