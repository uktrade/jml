import json
import logging
from typing import TYPE_CHECKING

from django.db.models.query import QuerySet

from activity_stream.models import ActivityStreamStaffSSOUser
from core.beis_service_now.models import ServiceNowUser

if TYPE_CHECKING:
    from django_stubs_ext import WithAnnotations


logger = logging.getLogger(__name__)


def ingest_service_now() -> None:
    # Only ingest users that are in the SSO, are NOT inactive and are NOT leavers.
    sso_users: QuerySet[WithAnnotations[ActivityStreamStaffSSOUser]] = (
        ActivityStreamStaffSSOUser.objects.active().not_a_leaver().with_emails().all()
    )

    for sso_user in sso_users:
        emails_to_try = [*sso_user.emails]
        if sso_user.service_now_user:
            previous_service_now_email = sso_user.service_now_user.email
            emails_to_try = [sso_user.service_now_user.email] + emails_to_try

        if not emails_to_try:
            continue

        emails_tried: set[str] = set()
        valid_email = None

        for email in emails_to_try:
            if not email or email in emails_tried:
                continue

            try:
                service_now_user = ServiceNowUser.objects.get(email=email)
            except ServiceNowUser.DoesNotExist:
                pass
            else:
                sso_user.service_now_user = service_now_user
                sso_user.save()

                valid_email = email

                break
            finally:
                emails_tried.add(email)

        logger.info(
            json.dumps(
                {
                    "sso_user": str(sso_user),
                    "previous_service_now_email": previous_service_now_email,
                    "emails": sso_user.emails,
                    "valid_email": valid_email,
                    "service_now_user_sys_id": sso_user.service_now_user.sys_id
                    if sso_user.service_now_user
                    else None,
                }
            )
        )
