import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone

from activity_stream.models import ActivityStreamStaffSSOUser
from core.utils.staff_index import (
    StaffDocumentNotFound,
    build_staff_document,
    get_staff_document_from_staff_index,
    index_staff_document,
)

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
            if not request.user.is_authenticated:
                return response

            user: User = request.user

            # Check if the ActivityStreamStaffSSOUser already exists
            as_users = ActivityStreamStaffSSOUser.objects.filter(
                contact_email_address=user.sso_contact_email,
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
                        "user_id": user.id,  # Would be legacy SSO id
                        "status": "active",
                        "last_accessed": timezone.now(),
                        "joined": timezone.now(),
                        "email_user_id": "",
                        "contact_email_address": user.sso_contact_email,
                        "became_inactive_on": None,
                    },
                )
            else:
                as_user = as_users.first()

            try:
                staff_document = get_staff_document_from_staff_index(
                    staff_id=as_user.identifier
                )
            except StaffDocumentNotFound:
                # Index ActivityStream object
                staff_document = build_staff_document(staff_sso_user=as_user)
                index_staff_document(staff_document=staff_document)

            # Mark the session as indexed
            request.session[self.SESSION_KEY] = True
            request.session.save()

        return response


class XRobotsTagMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Robots-Tag"] = "noindex,nofollow"

        return response
