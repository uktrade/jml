from django.core.management.base import BaseCommand

from employee_register.models import Position

import employee_register

class PositionStub:
    name = "Cost Centre Hierarchy"
    counter = 0

    def clear(self):
        Position.objects.all().delete()   

    def create(self):
        """Clear the Position tables, and create the stub data"""
        self.clear()
        Position.objects.create(title='Software Developer')
        Position.objects.create(title='Software Tester')
        Position.objects.create(title='Lead Developer')
        Position.objects.create(title='Delivery Manager')
        Position.objects.create(title='Program Manager')
        Position.objects.create(title='UX Developer')
        Position.objects.create(title='Product Manager')


class Command(BaseCommand):
    TEST_TYPE = {
        "Position": PositionStub,
    }

    help = "Create stub data. Allowed types are - All - {}".format(
        " - ".join(TEST_TYPE.keys())
    )
    arg_name = "what"

    def add_arguments(self, parser):
        # Positional arguments, default to All for no argument
        parser.add_argument(self.arg_name, nargs="*", default=["All"])

        # Named (optional) arguments
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete stub data instead of creating it",
        )

    def create(self, what):
        # The modified save writes the current user to the log, but
        # the user is not available while we are running a command.
        # So set  the test flag to stop writing to the log
        employee_register._called_from_test = True
        p = what()
        p.create()
        del employee_register._called_from_test
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully completed stub data creation for {}.".format(
                    p.name
                )
            )
        )

    def clear(self, what):
        employee_register._called_from_test = True
        p = what()
        p.clear()
        del employee_register._called_from_test
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully cleared stub data for {}.".format(
                    p.name
                )
            )
        )

    def handle(self, *args, **options):
        if options["delete"]:
            func = self.clear
        else:
            func = self.create
        for arg in options[self.arg_name]:
            if arg == "All":
                for t in self.TEST_TYPE.values():
                    func(t)
                return
            else:
                func(self.TEST_TYPE[arg])
