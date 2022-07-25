from typing import List, Optional

from django.conf import settings
from django.urls import reverse

from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from core import notify
from core.uksbs import get_uksbs_interface
from core.uksbs.types import PersonData
from leavers.exceptions import LeaverDoesNotHaveUKSBSPersonId
from leavers.models import LeaverInformation, LeavingRequest
from leavers.types import DisplayScreenEquipmentAsset


def send_leaver_thank_you_email(leaving_request: LeavingRequest):
    """
    Send the Leaver an email to thank them, and inform them of the next steps
    in the process.
    """
    assert leaving_request.leaver_activitystream_user
    leaver_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.leaver_activitystream_user
    )

    if not leaver_as_user.contact_email_address:
        raise ValueError("contact_email_address is not set")

    notify.email(
        email_addresses=[leaver_as_user.contact_email_address],
        template_id=notify.EmailTemplates.LEAVER_THANK_YOU_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "contact_us_link": "",  # TODO: Update when we have a contact form.
        },
    )


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

    if not leaver_information.leaver_date_of_birth:
        raise ValueError("leaver_date_of_birth is not set")

    notify.email(
        email_addresses=[settings.CSU4_EMAIL],
        template_id=notify.EmailTemplates.CSU4_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "date_of_birth": leaver_information.leaver_date_of_birth.strftime(
                "%d-%B-%Y %H:%M"
            ),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
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
        email_addresses=[settings.OCS_EMAIL],
        template_id=notify.EmailTemplates.OCS_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
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
        email_addresses=[settings.OCS_OAB_LOCKER_EMAIL],
        template_id=notify.EmailTemplates.OCS_OAB_LOCKER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
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

    leaver_email = leaving_request.get_leaver_email()

    if not leaver_email:
        raise ValueError("leaver_email is not set")

    notify.email(
        email_addresses=[],
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

    if not manager_as_user.contact_email_address:
        raise ValueError("contact_email_address is not set")

    notify.email(
        email_addresses=[manager_as_user.contact_email_address],
        template_id=notify.EmailTemplates.ROSA_LINE_MANAGER_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "manager_name": leaving_request.get_line_manager_name(),
        },
    )


def send_line_manager_correction_email(leaving_request: LeavingRequest):
    """
    Send an email to all of the Leaver's direct manager as per the response
    from UK SBS to get them to update the Line manager in UK SBS to match
    the LeavingRequest.
    """

    assert leaving_request.leaver_activitystream_user
    assert leaving_request.manager_activitystream_user

    leaver_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.leaver_activitystream_user
    )

    if not leaver_as_user.uksbs_person_id:
        raise LeaverDoesNotHaveUKSBSPersonId()

    uksbs_interface = get_uksbs_interface()

    uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
        person_id=leaver_as_user.uksbs_person_id,
    )

    uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get("manager", [])
    uksbs_leaver_manager_person_ids: List[str] = [
        str(uksbs_leaver_manager["person_id"])
        for uksbs_leaver_manager in uksbs_leaver_managers
    ]

    current_manager_emails: List[str] = []

    for current_manager_as_user in ActivityStreamStaffSSOUser.objects.filter(
        uksbs_person_id__in=uksbs_leaver_manager_person_ids
    ):
        current_manager_sso_email: Optional[
            ActivityStreamStaffSSOUserEmail
        ] = current_manager_as_user.sso_emails.first()

        if current_manager_sso_email:
            current_manager_emails.append(current_manager_sso_email.email_address)

    # If there are no manager emails, we need to email HR
    if not current_manager_emails:
        current_manager_emails = [settings.HR_UKSBS_CORRECTION_EMAIL]

    notify.email(
        email_addresses=current_manager_emails,
        template_id=notify.EmailTemplates.LINE_MANAGER_CORRECTION_EMAIL,
        personalisation={
            "recipient_name": current_manager_as_user.full_name,
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

    if not manager_as_user.contact_email_address:
        raise ValueError("contact_email_address is not set")

    notify.email(
        email_addresses=[manager_as_user.contact_email_address],
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

    if not manager_as_user.contact_email_address:
        raise ValueError("contact_email_address is not set")

    notify.email(
        email_addresses=[manager_as_user.contact_email_address],
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

    if not manager_as_user.contact_email_address:
        raise ValueError("contact_email_address is not set")

    notify.email(
        email_addresses=[manager_as_user.contact_email_address],
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
        email_addresses=[settings.SECURITY_TEAM_EMAIL],
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
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
        email_addresses=[settings.SECURITY_TEAM_EMAIL],
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
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
        email_addresses=[settings.SRE_EMAIL],
        template_id=notify.EmailTemplates.SRE_REMINDER_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
            "sre_team_link": reverse("sre-confirmation", args=[leaving_request.uuid]),
        },
    )


def send_it_ops_asset_email(leaving_request: LeavingRequest):
    """
    Send IT Ops team an email to inform them of a leaver and their reported Assets.
    """

    if not settings.IT_OPS_EMAIL:
        raise ValueError("IT_OPS_EMAIL is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    dse_assets: List[DisplayScreenEquipmentAsset] = leaver_information.dse_assets
    dse_assets_string = ""
    for dse_asset in dse_assets:
        dse_asset_name = dse_asset["name"]
        dse_assets_string += f"* {dse_asset_name}\n"

    notify.email(
        email_addresses=[settings.IT_OPS_EMAIL],
        template_id=notify.EmailTemplates.IT_OPS_ASSET_EMAIL,
        personalisation={
            "leaver_name": leaving_request.get_leaver_name(),
            "leaving_date": leaver_information.leaving_date.strftime("%d-%B-%Y %H:%M"),
            "dse_assets": dse_assets_string,
        },
    )
