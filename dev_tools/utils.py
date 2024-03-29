import uuid
from typing import TYPE_CHECKING, Optional, Tuple

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.utils import timezone

from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from core.utils.staff_index import build_staff_document, update_staff_document

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


def create_user(
    first_name: str, last_name: str, email: str, group: Optional[Group] = None
) -> Tuple["User", bool, ActivityStreamStaffSSOUser]:
    created = False
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Create the new user
        user = User.objects.create(
            username=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        uuid_str = str(uuid.uuid4())
        user.sso_legacy_user_id = uuid_str
        user.sso_email_user_id = f"test@{uuid_str}.com"
        user.set_password("password")
        user.save()
        created = True

    if group:
        user.groups.add(group)

    staff_sso_user, _ = ActivityStreamStaffSSOUser.objects.get_or_create(
        email_user_id=user.sso_email_user_id,
        defaults={
            "identifier": str(uuid.uuid4()),
            "name": f"{user.first_name} {user.last_name}",
            "obj_type": "dit:StaffSSO:User",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_id": user.sso_legacy_user_id,
            "status": "active",
            "last_accessed": timezone.now(),
            "joined": timezone.now(),
            "contact_email_address": user.sso_contact_email,
            "email_user_id": user.sso_email_user_id,
            "available": True,
            "uksbs_person_id": str(uuid.uuid4()),
        },
    )

    ActivityStreamStaffSSOUserEmail.objects.get_or_create(
        staff_sso_user=staff_sso_user,
        email_address=user.email,
    )

    # Add the user into the Staff Index
    staff_document = build_staff_document(staff_sso_user=staff_sso_user)
    staff_document.uuid = str(uuid.uuid4())
    update_staff_document(
        staff_document.staff_sso_email_user_id,
        staff_document=staff_document.to_dict(),
        upsert=True,
    )

    return user, created, staff_sso_user


def change_user(request: HttpRequest, user_pk: Optional[str]) -> None:
    if user_pk:
        new_user = User.objects.get(pk=user_pk)

        login(request, new_user, backend="django.contrib.auth.backends.ModelBackend")
    else:
        logout(request)
