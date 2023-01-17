from typing import Dict, List, Optional

from django.conf import settings
from django.db.models.query import QuerySet
from django.urls import reverse

from activity_stream.models import ActivityStreamStaffSSOUser
from core import notify
from core.uksbs import get_uksbs_interface
from core.uksbs.types import PersonData
from core.utils.helpers import DATE_FORMAT_STR, make_possessive
from leavers.exceptions import LeaverDoesNotHaveUKSBSPersonId
from leavers.models import LeaverInformation, LeavingRequest
from leavers.types import DisplayScreenEquipmentAsset


def get_leaving_request_email_personalisation(
    leaving_request: LeavingRequest,
) -> Dict[str, str]:
    """
    Build the personalisation dictionary for the email.

    leaver_name: The name of the leaver
    leaver_email: The email address of the leaver
    possessive_leaver_name: The name of the leaver in possessive form
    date_of_birth: The date of birth of the leaver

    manager_name: The name of the Line Manager
    manager_email: The email address of the Line Manager

    leaving_date: The date the leaver is leaving
    last_day: The last day of the leaver

    has_data_recipient: Whether the leaver has a data recipient
    data_recipient_name: The name of the data recipient
    data_recipient_email: The email address of the data recipient

    contact_us_link: The link to the contact us page
    line_manager_link: The link for the line manager to continue the process
    line_manager_thank_you_link: The link for the thank you page for the line manager
    line_manager_offline_service_now_details_link: The link for the line manager
        to mark that the leaver has been submitted into Service Now.
    security_team_bp_link: The link for the security team to mark the building pass status
    security_team_rk_link: The link for the security team to mark the rosa kit status
    sre_team_link: The link for the SRE team to mark the SRE status

    """

    personalisation: Dict[str, str] = {}

    leaver_name = leaving_request.get_leaver_name()
    assert leaver_name

    leaver_email = leaving_request.get_leaver_email()
    assert leaver_email

    leaving_date = leaving_request.get_leaving_date()
    assert leaving_date

    last_day = leaving_request.get_last_day()
    assert last_day

    manager_as_user = leaving_request.get_line_manager()
    assert manager_as_user

    site_url = settings.SITE_URL

    personalisation.update(
        leaver_name=leaver_name,
        leaver_email=leaver_email,
        possessive_leaver_name=make_possessive(leaver_name),
        manager_name=manager_as_user.full_name,
        manager_email=manager_as_user.get_email_addresses_for_contact()[0],
        leaving_date=leaving_date.strftime(DATE_FORMAT_STR),
        last_day=last_day.strftime(DATE_FORMAT_STR),
        has_data_recipient="no",
        data_recipient_name="",
        data_recipient_email="",
        contact_us_link=site_url + reverse("beta-service-feedback"),
        line_manager_link=site_url
        + reverse(
            "line-manager-start",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
        line_manager_thank_you_link=site_url
        + reverse(
            "line-manager-thank-you",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
        line_manager_offline_service_now_details_link=site_url
        + reverse(
            "line-manager-offline-service-now-details",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
        security_team_bp_link=site_url
        + reverse(
            "security-team-building-pass-confirmation",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
        security_team_rk_link=site_url
        + reverse(
            "security-team-rosa-kit-confirmation",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
        sre_team_link=site_url
        + reverse(
            "sre-detail",
            kwargs={"leaving_request_uuid": leaving_request.uuid},
        ),
    )

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    if not leaver_information.leaver_date_of_birth:
        raise ValueError("leaver_date_of_birth is not set")

    personalisation.update(
        date_of_birth=leaver_information.leaver_date_of_birth.strftime(DATE_FORMAT_STR),
    )

    if leaving_request.data_recipient_activitystream_user:
        data_recipient = leaving_request.data_recipient_activitystream_user
        primary_email: str = data_recipient.get_primary_email() or ""
        personalisation.update(
            has_data_recipient="yes",
            data_recipient_name=data_recipient.full_name,
            data_recipient_email=primary_email,
        )

    return personalisation


def send_leaver_thank_you_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send the Leaver an email to thank them, and inform them of the next steps
    in the process.
    """
    assert leaving_request.leaver_activitystream_user
    leaver_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.leaver_activitystream_user
    )

    contact_emails = leaver_as_user.get_email_addresses_for_contact()
    if not contact_emails:
        raise ValueError("Can't get contact email for the Leaver")

    personalisation = get_leaving_request_email_personalisation(leaving_request)
    notify.email(
        email_addresses=contact_emails,
        template_id=notify.EmailTemplates.LEAVER_THANK_YOU_EMAIL,
        personalisation=personalisation,
    )


def send_leaver_not_in_uksbs_reminder(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send email to inform HR that a leaver is not in UK SBS.
    """
    assert leaving_request.manager_activitystream_user
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    manager_emails = manager_as_user.get_email_addresses_for_contact()

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    # HR Email
    notify.email(
        email_addresses=[settings.HR_UKSBS_CORRECTION_EMAIL],
        template_id=notify.EmailTemplates.LEAVER_NOT_IN_UKSBS_HR_REMINDER,
        personalisation=personalisation | {"recipient_name": "DIT Offboarding Team"},
    )
    # Line Manager email
    notify.email(
        email_addresses=manager_emails,
        template_id=notify.EmailTemplates.LEAVER_NOT_IN_UKSBS_LM_REMINDER,
        personalisation=personalisation | {"recipient_name": manager_as_user.full_name},
    )


def send_clu4_leaver_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Cluster 4 Email to notify of a new leaver.
    """

    if not settings.CLU4_EMAIL:
        raise ValueError("CLU4_EMAIL is not set")

    if not settings.SECURITY_TEAM_VETTING_EMAIL:
        raise ValueError("SECURITY_TEAM_VETTING_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.CLU4_EMAIL, settings.SECURITY_TEAM_VETTING_EMAIL],
        template_id=notify.EmailTemplates.CLU4_LEAVER_EMAIL,
        personalisation=personalisation,
    )


def send_ocs_leaver_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send OCS Email to notify of a new leaver.
    """

    if not settings.OCS_EMAIL:
        raise ValueError("OCS_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.OCS_EMAIL],
        template_id=notify.EmailTemplates.OCS_LEAVER_EMAIL,
        personalisation=personalisation,
    )


def send_ocs_oab_locker_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send OCS OAB Locker email.
    """

    if not settings.OCS_OAB_LOCKER_EMAIL:
        raise ValueError("OCS_OAB_LOCKER_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.OCS_OAB_LOCKER_EMAIL],
        template_id=notify.EmailTemplates.OCS_OAB_LOCKER_EMAIL,
        personalisation=personalisation,
    )


def send_comaea_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send OCS OAB Locker email.
    """

    if not settings.COMAEA_EMAIL:
        raise ValueError("COMAEA_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.COMAEA_EMAIL],
        template_id=notify.EmailTemplates.COMAEA_EMAIL,
        personalisation=personalisation,
    )


def send_line_manager_correction_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send an email to all of the Leaver's direct manager as per the response
    from UK SBS to get them to update the Line Manager in UK SBS to match
    the LeavingRequest.
    """

    assert leaving_request.leaver_activitystream_user
    assert leaving_request.manager_activitystream_user

    leaver_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.leaver_activitystream_user
    )
    manager_as_user: ActivityStreamStaffSSOUser = (
        leaving_request.manager_activitystream_user
    )

    leaver_person_id = leaver_as_user.get_person_id()
    if not leaver_person_id:
        raise LeaverDoesNotHaveUKSBSPersonId()

    uksbs_interface = get_uksbs_interface()

    uksbs_leaver_hierarchy = uksbs_interface.get_user_hierarchy(
        person_id=leaver_person_id,
    )

    uksbs_leaver_managers: List[PersonData] = uksbs_leaver_hierarchy.get("manager", [])
    uksbs_leaver_manager_person_ids: List[str] = [
        str(uksbs_leaver_manager["person_id"])
        for uksbs_leaver_manager in uksbs_leaver_managers
    ]
    current_manager_as_users: QuerySet[
        ActivityStreamStaffSSOUser
    ] = ActivityStreamStaffSSOUser.objects.active().filter_by_person_id(
        uksbs_leaver_manager_person_ids
    )

    email_personalisation = get_leaving_request_email_personalisation(leaving_request)
    email_personalisation = email_personalisation | {
        "manager_name": manager_as_user.full_name
    }

    if current_manager_as_users.exists():
        for current_manager_as_user in current_manager_as_users:
            current_manager_contact_emails = (
                current_manager_as_user.get_email_addresses_for_contact()
            )
            if current_manager_contact_emails:
                # Send email to UKSBS manager(s)
                notify.email(
                    email_addresses=current_manager_contact_emails,
                    template_id=notify.EmailTemplates.LINE_MANAGER_CORRECTION_EMAIL,
                    personalisation=email_personalisation
                    | {"recipient_name": current_manager_as_user.full_name},
                )
    else:
        # If there are no manager emails, we need to email the HR Offboarding
        # team and the Line Manager that the Leaver selected.
        manager_contact_emails = manager_as_user.get_email_addresses_for_contact()
        if not manager_contact_emails:
            raise ValueError("manager_contact_emails is not set")

        if not settings.HR_UKSBS_CORRECTION_EMAIL:
            raise ValueError("HR_UKSBS_CORRECTION_EMAIL is not set")

        notify.email(
            email_addresses=manager_contact_emails,
            template_id=notify.EmailTemplates.LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL,
            personalisation=email_personalisation
            | {"recipient_name": manager_as_user.full_name},
        )

        notify.email(
            email_addresses=[settings.HR_UKSBS_CORRECTION_EMAIL],
            template_id=notify.EmailTemplates.LINE_MANAGER_CORRECTION_HR_EMAIL,
            personalisation=email_personalisation
            | {"recipient_name": "HR Offboarding team"},
        )


def send_line_manager_notification_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Line Manager an email to notify them of a Leaver they need to process.
    """
    manager_as_user = leaving_request.get_line_manager()
    assert manager_as_user

    manager_contact_emails = manager_as_user.get_email_addresses_for_contact()
    if not manager_contact_emails:
        raise ValueError("manager_contact_emails is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=manager_contact_emails,
        template_id=notify.EmailTemplates.LINE_MANAGER_NOTIFICATION_EMAIL,
        personalisation=personalisation,
    )


def send_line_manager_reminder_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Line Manager a reminder email to notify them of a Leaver they need to process.
    """
    manager_as_user = leaving_request.get_line_manager()
    assert manager_as_user

    manager_contact_emails = manager_as_user.get_email_addresses_for_contact()
    if not manager_contact_emails:
        raise ValueError("manager_contact_emails is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=manager_contact_emails,
        template_id=notify.EmailTemplates.LINE_MANAGER_REMINDER_EMAIL,
        personalisation=personalisation,
    )


def send_line_manager_thankyou_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Line Manager a thank you email.
    """
    manager_as_user = leaving_request.get_line_manager()
    assert manager_as_user

    manager_contact_emails = manager_as_user.get_email_addresses_for_contact()
    if not manager_contact_emails:
        raise ValueError("manager_contact_emails is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=manager_contact_emails,
        template_id=notify.EmailTemplates.LINE_MANAGER_THANKYOU_EMAIL,
        personalisation=personalisation,
    )


def send_line_manager_offline_service_now_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Line Manager a thank you email.
    """
    manager_as_user = leaving_request.get_line_manager()
    assert manager_as_user

    manager_contact_emails = manager_as_user.get_email_addresses_for_contact()
    if not manager_contact_emails:
        raise ValueError("manager_contact_emails is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=manager_contact_emails,
        template_id=notify.EmailTemplates.LINE_MANAGER_OFFLINE_SERVICE_NOW_EMAIL,
        personalisation=personalisation,
    )


def send_security_team_offboard_bp_leaver_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Security Team an email to inform them of a new leaver to be offboarded.
    """

    if not settings.SECURITY_TEAM_BUILDING_PASS_EMAIL:
        raise ValueError("SECURITY_TEAM_BUILDING_PASS_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.SECURITY_TEAM_BUILDING_PASS_EMAIL],
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL,
        personalisation=personalisation,
    )


def send_security_team_offboard_rk_leaver_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Security Team an email to inform them of a new leaver to be offboarded.
    """

    if not settings.SECURITY_TEAM_ROSA_EMAIL:
        raise ValueError("SECURITY_TEAM_ROSA_EMAIL is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.SECURITY_TEAM_ROSA_EMAIL],
        template_id=notify.EmailTemplates.SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL,
        personalisation=personalisation,
    )


def send_sre_notification_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send the SRE team an email to inform them of a new leaver to be offboarded.
    """
    # Skip this task
    pass

    # if not settings.SRE_EMAIL:
    #     raise ValueError("SRE_EMAIL is not set")

    # personalisation = get_leaving_request_email_personalisation(leaving_request)

    # notify.email(
    #     email_addresses=[settings.SRE_EMAIL],
    #     template_id=notify.EmailTemplates.SRE_NOTIFICATION,
    #     personalisation=personalisation,
    # )


def send_it_ops_asset_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send IT Ops team an email to inform them of a leaver and their reported Assets.
    """

    if not settings.IT_OPS_EMAIL:
        raise ValueError("IT_OPS_EMAIL is not set")

    leaving_date = leaving_request.get_leaving_date()
    if not leaving_date:
        raise ValueError("leaving_date is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    dse_assets_string = ""
    dse_assets: Optional[
        List[DisplayScreenEquipmentAsset]
    ] = leaver_information.dse_assets
    if dse_assets:
        for dse_asset in dse_assets:
            dse_asset_name = dse_asset["name"]
            dse_assets_string += f"* {dse_asset_name}\n"

    personalisation = get_leaving_request_email_personalisation(leaving_request)
    personalisation.update(dse_assets=dse_assets_string)

    notify.email(
        email_addresses=[settings.IT_OPS_EMAIL],
        template_id=notify.EmailTemplates.IT_OPS_ASSET_EMAIL,
        personalisation=personalisation,
    )


def send_feetham_security_pass_office_email(
    leaving_request: LeavingRequest,
    template_id: Optional[notify.EmailTemplates] = None,
):
    """
    Send Feetham Security Pass Office an email to inform them of a leaver.
    """

    if not settings.FEETHAM_SECURITY_PASS_OFFICE_EMAIL:
        raise ValueError("FEETHAM_SECURITY_PASS_OFFICE_EMAIL is not set")

    leaving_date = leaving_request.get_leaving_date()
    if not leaving_date:
        raise ValueError("leaving_date is not set")

    leaver_information: Optional[
        LeaverInformation
    ] = leaving_request.leaver_information.first()

    if not leaver_information:
        raise ValueError("leaver_information is not set")

    personalisation = get_leaving_request_email_personalisation(leaving_request)

    notify.email(
        email_addresses=[settings.FEETHAM_SECURITY_PASS_OFFICE_EMAIL],
        template_id=notify.EmailTemplates.FEETHAM_SECURITY_PASS_OFFICE_EMAIL,
        personalisation=personalisation,
    )


def send_leaver_list_pay_cut_off_reminder(leaving_requests: QuerySet[LeavingRequest]):
    """
    Send email to inform HR that an incomplete leaver will leave before
    the next pay cut off period
    """
    if leaving_requests.count() == 0:
        return

    if not settings.HR_UKSBS_CORRECTION_EMAIL:
        raise ValueError("HR_UKSBS_CORRECTION_EMAIL is not set")

    personalisation: Dict[str, str] = {}

    leaver_name_list_string = ""
    for leaving_request in leaving_requests:
        leaver_name_list_string += f"* {leaving_request.get_leaver_name()}\n"

    personalisation.update(leaver_name_list=leaver_name_list_string)

    notify.email(
        email_addresses=[settings.HR_UKSBS_CORRECTION_EMAIL],
        template_id=notify.EmailTemplates.LEAVER_IN_PAY_CUT_OFF_HR_EMAIL,
        personalisation=personalisation,
    )
