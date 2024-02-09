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

        current_sn_users = sso_user.service_now_users.all()
        sn_users = ServiceNowUser.objects.filter(email__in=emails_to_try)
        new_sn_users = sn_users.exclude(
            sys_id__in=current_sn_users.values_list("sys_id")
        )
        old_sn_users = current_sn_users.exclude(
            sys_id__in=sn_users.values_list("sys_id")
        )

        for new_sn_user in new_sn_users:
            sso_user.service_now_users.add(new_sn_user)
        for old_sn_user in old_sn_users:
            sso_user.service_now_users.remove(old_sn_user)
        sso_user.save()

        logger.info(
            json.dumps(
                {
                    "sso_user": str(sso_user),
                    "emails": sso_user.emails,
                    "new_sn_emails": list(new_sn_users.values_list("email", flat=True)),
                    "old_sn_emails": list(old_sn_users.values_list("email", flat=True)),
                    "sn_emails": list(
                        sso_user.service_now_users.all().values_list("email", flat=True)
                    ),
                }
            )
        )


def json_load_list(post_body: bytes) -> list:
    post_body = post_body.decode()

    # NOTE: This is a hack to remove the quotes from the body since the
    # ServiceNow request sends the body as a string.
    if post_body.startswith('"') and post_body.endswith('"'):
        post_body = post_body[1:-1]

    post_body = json.loads(post_body)

    # TODO: Remove this debug exception
    logger.exception(
        Exception(
            f"""
            POST request received!

            post_body: {post_body}
            """
        )
    )

    if not isinstance(post_body, list):
        raise ValueError(f"Expected a list of objects, got {type(post_body)}")

    return post_body
