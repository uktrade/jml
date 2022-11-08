from dev_tools.utils import create_user
from django.contrib.auth import get_user_model

User = get_user_model()


def create_users_for_testing(first_name: str, last_name: str):
    leaver_email = f"{first_name}.{last_name}@example.com"  # /PS-IGNORE
    manager_email = f"{first_name}.linemanager.{last_name}@example.com"  # /PS-IGNORE

    if User.objects.filter(email=leaver_email).exists():
        raise Exception(f"User already exists with email {leaver_email}")
    if User.objects.filter(email=manager_email).exists():
        raise Exception(f"User already exists with email {manager_email}")

    # Create the leaver
    create_user(
        first_name=first_name,
        last_name=last_name,
        email=leaver_email,
    )
    # Create their Line manager
    create_user(
        first_name=first_name,
        last_name=f"line manager {last_name}",
        email=manager_email,
    )
