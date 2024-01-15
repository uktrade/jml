#!/usr/bin/env python
import os
import sys


def initialize_debugpy():
    try:
        import debugpy
    except ImportError:
        sys.stdout.write(
            "debugpy is not installed, please install it with: pip install debugpy\n"
        )
        return

    # RUN_MAIN is set to a truthy value in the subprocesses started by the
    # reloader. This check ensures that debugpy is only started in the main process.
    if not os.getenv("RUN_MAIN"):
        debugpy.listen(("0.0.0.0", 5678))
        sys.stdout.write("debugpy listening on port 5678...\n")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    from django.conf import settings

    if settings.DEBUG and settings.ENABLE_DEBUGPY:
        initialize_debugpy()

    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
