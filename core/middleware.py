import uuid
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils import timezone

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    StaffDocumentNotFound,
    build_staff_document,
    get_staff_document_from_staff_index,
    update_staff_document,
)

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class IndexCurrentUser:
    SESSION_KEY = "current_user_indexed"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        DO NOT USE ON PRODUCTION

        Adds the given user to the ActivityStream and Staff Index
        """

        response = self.get_response(request)

        assert hasattr(request, "user")
        assert hasattr(request, "session")

        if not request.session.get(self.SESSION_KEY, False):
            # Check if the user is authenticated
            if not (
                request.user
                and request.user.is_authenticated
                and not request.user.is_anonymous
            ):
                return response

            user: User = request.user

            # Check if the ActivityStreamStaffSSOUser already exists
            as_users: QuerySet[
                ActivityStreamStaffSSOUser
            ] = ActivityStreamStaffSSOUser.objects.active().filter(
                email_user_id=user.sso_email_user_id,
            )
            if not as_users.exists():
                # Create ActivityStream object
                (as_user, _,) = ActivityStreamStaffSSOUser.objects.update_or_create(
                    identifier=uuid.uuid4(),
                    defaults={
                        "available": True,
                        "name": f"{user.first_name} {user.last_name}",
                        "obj_type": "dit:StaffSSO:User",
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "user_id": user.sso_legacy_user_id,
                        "status": "active",
                        "last_accessed": timezone.now(),
                        "joined": timezone.now(),
                        "email_user_id": user.sso_email_user_id,
                        "contact_email_address": user.sso_contact_email,
                        "became_inactive_on": None,
                    },
                )
            else:
                as_user = as_users.first()

            try:
                get_staff_document_from_staff_index(
                    sso_email_user_id=as_user.email_user_id,
                )
            except StaffDocumentNotFound:
                # Index ActivityStream object
                staff_document = build_staff_document(staff_sso_user=as_user)
                update_staff_document(
                    id=staff_document.staff_sso_email_user_id,
                    staff_document=staff_document.to_dict(),
                    upsert=True,
                )

            # Mark the session as indexed
            request.session[self.SESSION_KEY] = True
            request.session.save()

        return response


class PrimaryEmailMiddleware:
    url_name = "choose_primary_email"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        resolved_path = resolve(request.path)
        if resolved_path.url_name == self.url_name:
            return self.get_response(request)

        user = request.user
        if user.is_anonymous:
            return self.get_response(request)

        try:
            activitystream_user = ActivityStreamStaffSSOUser.objects.active().get(
                email_user_id=user.sso_email_user_id,
            )
        except ActivityStreamStaffSSOUser.DoesNotExist:
            pass
        else:
            sso_emails = activitystream_user.sso_emails.all()
            if len(sso_emails) > 1 and not sso_emails.filter(is_primary=True).exists():
                return redirect(reverse(self.url_name) + "?next=" + request.path)

        return self.get_response(request)
