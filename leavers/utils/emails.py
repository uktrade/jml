from typing import Optional

from django.conf import settings
from django.urls import reverse

from activity_stream.models import ActivityStreamStaffSSOUser
from core import notify
from leavers.models import LeaverInformation, LeavingRequest


def send_csu4_leaver_email(leaving_request: LeavingRequest):
    """
    Send Cluster 4 Email to notify of a new leaver.

    The data sent in this email is Sensitive and Personal.
    Only add more information to this email if it is absolutely necessary.

    Currently included data:
    - Leaver Name
    """

    if not settings.CSU4_EMAIL:
        raise ValueError("CSU4_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.CSU4_EMAIL,
        template_id=notify.EmailTemplates.CSU4_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "date_of_birth": "TO REMOVE",
            "leaving_date": leaver_information.leaving_date,
        },
    )


def send_ocs_leaver_email(leaving_request: LeavingRequest):
    """
    Send OCS Email to notify of a new leaver.

    The data sent in this email is Sensitive and Personal.
    Only add more information to this email if it is absolutely necessary.

    Currently included data:
    - Leaver Name
    """

    if not settings.OCS_EMAIL:
        raise ValueError("OCS_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.OCS_EMAIL,
        template_id=notify.EmailTemplates.OCS_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date,
        },
    )


def send_ocs_oab_locker_email(leaving_request: LeavingRequest):
    """
    Send OCS OAB Locker email.

    The data sent in this email is Sensitive and Personal.
    Only add more information to this email if it is absolutely necessary.

    Currently included data:
    - Leaver Name
    """

    if not settings.OCS_OAB_LOCKER_EMAIL:
        raise ValueError("OCS_OAB_LOCKER_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.OCS_OAB_LOCKER_EMAIL,
        template_id=notify.EmailTemplates.OCS_OAB_LOCKER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date,
        },
    )


class LeaverDoesNotHaveRosaKit(Exception):
    pass


def send_rosa_leaver_reminder_email(leaving_request: LeavingRequest):
    """
    Send Leaver an email to remind them to return their ROSA Kit.
    """

    if not leaving_request.is_rosa_user:
        raise LeaverDoesNotHaveRosaKit()

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=leaver_information.leaver_email,
        template_id=notify.EmailTemplates.ROSA_LEAVER_REMINDER_EMAIL,
        personalisation={"leaver_name": leaving_request.get_leaver_name()},
    )


def send_rosa_line_manager_reminder_email(leaving_request: LeavingRequest):
    """
    Send Line Manager an email to remind the Leaver to return their ROSA Kit.
    """

    if not leaving_request.is_rosa_user:
        raise LeaverDoesNotHaveRosaKit()

    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    notify.email(
        email_address=manager_as_user.email_address,
        template_id=notify.EmailTemplates.ROSA_LINE_MANAGER_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
        },
    )


def send_line_manager_correction_email(leaving_request: LeavingRequest):
    """
    Send ??? an email to get them to update the Line manager in UK SBS to match the LeavingRequest.
    """

    if not leaving_request.is_rosa_user:
        raise LeaverDoesNotHaveRosaKit()

    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    notify.email(
        email_address=manager_as_user.email_address,
        template_id=notify.EmailTemplates.LINE_MANAGER_CORRECTION_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
        },
    )


def send_line_manager_notification_email(leaving_request: LeavingRequest):
    """
    Send Line Manager an email to notify them of a Leaver they need to process.
    """
    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    notify.email(
        email_address=manager_as_user.email_address,
        template_id=notify.EmailTemplates.LINE_MANAGER_NOTIFICATION_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
            "line_manager_link": reverse(
                "line-manager-start", args=[leaving_request.uuid]
            ),
        },
    )


def send_line_manager_reminder_email(leaving_request: LeavingRequest):
    """
    Send Line Manager a reminder email to notify them of a Leaver they need to process.
    """
    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    notify.email(
        email_address=manager_as_user.email_address,
        template_id=notify.EmailTemplates.LINE_MANAGER_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
            "line_manager_link": reverse(
                "line-manager-start", args=[leaving_request.uuid]
            ),
        },
    )


def send_line_manager_thankyou_email(leaving_request: LeavingRequest):
    """
    Send Line Manager a thank you email.
    """
    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    notify.email(
        email_address=manager_as_user.email_address,
        template_id=notify.EmailTemplates.LINE_MANAGER_THANKYOU_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
        },
    )


def send_security_team_offboard_leaver_email(leaving_request: LeavingRequest):
    """
    Send Security Team an email to inform them of a new leaver to be off-boarded.
    """

    if not settings.SECURITY_TEAM_EMAIL:
        raise ValueError("SECURITY_TEAM_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.SECURITY_TEAM_EMAIL,
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date,
            "security_team_link": reverse(
                "security-team-confirmation", args=[leaving_request.uuid]
            ),
        },
    )


def send_security_team_offboard_leaver_reminder_email(leaving_request: LeavingRequest):
    """
    Send Security Team an email to remind them of a leaver to be offboarded.
    """

    if not settings.SECURITY_TEAM_EMAIL:
        raise ValueError("SECURITY_TEAM_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.SECURITY_TEAM_EMAIL,
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date,
            "security_team_link": reverse(
                "security-team-confirmation", args=[leaving_request.uuid]
            ),
        },
    )


def send_sre_reminder_email(leaving_request: LeavingRequest):
    """
    Send SRE Team an email to remind them of a leaver.
    """

    if not settings.SRE_EMAIL:
        raise ValueError("SRE_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    notify.email(
        email_address=settings.SRE_EMAIL,
        template_id=notify.EmailTemplates.SRE_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date,
            "sre_team_link": reverse("sre-confirmation", args=[leaving_request.uuid]),
        },
    )
