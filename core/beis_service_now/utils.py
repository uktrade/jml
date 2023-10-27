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
        if not emails_to_try:
            continue

        sn_users = ServiceNowUser.objects.filter(email__in=emails_to_try)

        if sn_users:
            for sn_user in sn_users:
                sso_user.service_now_users.add(sn_user)
            sso_user.save()

        logger.info(
            json.dumps(
                {
                    "sso_user": str(sso_user),
                    "emails": sso_user.emails,
                    "sn_emails": sso_user.service_now_users.all().values_list(
                        "email", flat=True
                    ),
                }
            )
        )
