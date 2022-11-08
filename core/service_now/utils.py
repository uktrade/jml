import json
import logging
from typing import TYPE_CHECKING, Optional

from django.db.models.query import QuerySet

from activity_stream.models import ActivityStreamStaffSSOUser
from core.service_now import get_service_now_interface
from core.service_now.interfaces import ServiceNowUserNotFound

if TYPE_CHECKING:
    from django_stubs_ext import WithAnnotations


logger = logging.getLogger(__name__)


def ingest_service_now() -> None:
    service_now_interface = get_service_now_interface()

    # Only ingest users that are in the SSO, are NOT inactive and are NOT leavers.
    sso_users: QuerySet[WithAnnotations[ActivityStreamStaffSSOUser]] = (
        ActivityStreamStaffSSOUser.objects.active().not_a_leaver().with_emails().all()
    )

    for sso_user in sso_users:
        service_now_email: Optional[str] = sso_user.service_now_email_address

        emails_to_try = [service_now_email, *sso_user.emails]

        if not emails_to_try:
            continue

        emails_tried: set[str] = set()
        valid_email = None

        for email in emails_to_try:
            if not email or email in emails_tried:
                continue

            try:
                service_now_user = service_now_interface.get_user(email=email)
            except ServiceNowUserNotFound:
                pass
            else:
                sso_user.service_now_user_id = service_now_user["sys_id"]
                sso_user.service_now_email_address = email
                sso_user.save()

                valid_email = email

                break
            finally:
                emails_tried.add(email)

        logger.info(
            json.dumps(
                {
                    "sso_user": str(sso_user),
                    "previous_service_now_email": service_now_email,
                    "emails": sso_user.emails,
                    "valid_email": valid_email,
                    "service_now_user_id": sso_user.service_now_user_id,
                    "service_now_email_address": sso_user.service_now_email_address,
                }
            )
        )
