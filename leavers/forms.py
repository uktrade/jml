import datetime
from typing import Dict, List

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile  # /PS-IGNORE

from core.forms import GovFormattedForm, GovFormattedModelForm
from core.service_now import get_service_now_interface
from leavers.models import LeavingRequest, ReturnOption
from leavers.widgets import DateSelectorWidget


class LeaversForm(GovFormattedForm):
    for_self = forms.BooleanField(
        label="I am leaving the DIT (leave blank if filling in for someone else)",
        required=False,
    )
    leaver_email_address = forms.EmailField(
        label="Email address of leaver (if not you)",
        required=False,
    )
    last_day = forms.DateField(
        label="When is the leavers last day?",
        initial=datetime.date.today,
        widget=DateSelectorWidget(),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        for_self = cleaned_data.get("for_self")
        leaver_email_address = cleaned_data.get("leaver_email_address")

        if not for_self and not leaver_email_address:
            raise ValidationError(
                "If you are leaving the DIT, please check the 'I am "
                "leaving DIT' checkbox. If you are filling this form "
                "out for someone else, please provide their email "
                "address"
            )


class HardwareReceivedForm(GovFormattedModelForm):
    class Meta:
        model = LeavingRequest
        fields = ("hardware_received",)


class SREConfirmCompleteForm(GovFormattedForm):
    vpn = forms.BooleanField(
        label="VPN",
        required=True,
    )
    govuk_paas = forms.BooleanField(
        label="GOVUK PAAS",
        required=True,
    )
    github = forms.BooleanField(
        label="Github, removed from teams and repos",
        required=False,
    )
    sentry = forms.BooleanField(
        required=False,
    )
    slack = forms.BooleanField(
        required=False,
    )
    sso = forms.BooleanField(
        label="SSO",
        required=True,
    )
    aws = forms.BooleanField(
        label="AWS",
        required=True,
    )
    jira = forms.BooleanField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_message_replacement: Dict[str, str] = {
            "vpn": "VPN",
            "govuk_paas": "GOVUK PAAS",
            "sso": "SSO",
            "aws": "AWS",
            "jira": "Jira",
        }
        for field_name, field in self.fields.items():
            if field_name in required_message_replacement:
                message_replacement = required_message_replacement[field_name]
                field.error_messages[
                    "required"
                ] = f"Select {message_replacement} to confirm removal."


class LeaverOrLineManagerForm(GovFormattedForm):
    pass


class ContactForm(forms.Form):
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        pass


class WhoIsLeavingForm(GovFormattedForm):
    CHOICES = [
        ("me", "Me"),
        ("someone_else", "Someone Else"),
    ]

    who_for = forms.ChoiceField(
        label="",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
    )

    last_day = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=False,
    )


class SearchForm(GovFormattedForm):
    search_terms = forms.CharField(label="Find the leaver using their name or email")


class PersonNotFoundForm(GovFormattedForm):
    email = forms.EmailField(
        label="Can't see the person you're looking for? Enter their email:"
    )


class LeaverConfirmationForm(GovFormattedForm):
    last_day = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=False,
    )


class LeaverUpdateForm(GovFormattedForm):
    # Personal details
    first_name = forms.CharField(label="First name")  # /PS-IGNORE
    last_name = forms.CharField(label="Last name")  # /PS-IGNORE
    personal_email = forms.EmailField(label="Email")
    personal_phone = forms.CharField(label="Phone", max_length=16)
    personal_address = forms.CharField(
        label="Address",
        widget=forms.Textarea,
    )
    # Professional details
    grade = forms.CharField(label="Grade")
    job_title = forms.CharField(label="Job title")
    directorate = forms.ChoiceField(label="Directorate", choices=[])
    department = forms.ChoiceField(label="Department", choices=[])
    work_email = forms.EmailField(label="Email")
    manager = forms.ChoiceField(label="Manager", choices=[])
    staff_id = forms.CharField(label="Staff ID")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_now_interface = get_service_now_interface()
        service_now_directorates = service_now_interface.get_directorates()
        if not service_now_directorates:
            raise Exception("No directorates returned from Service Now")
        service_now_departments = service_now_interface.get_departments()
        if not service_now_departments:
            raise Exception("No departments returned from Service Now")
        service_now_managers = service_now_interface.get_active_line_managers()
        if not service_now_managers:
            raise Exception("No line managers returned from Service Now")

        self.fields["directorate"].choices = [
            (directorate["sys_id"], directorate["name"])
            for directorate in service_now_directorates
        ]
        self.fields["department"].choices = [
            (department["sys_id"], department["name"])
            for department in service_now_departments
        ]
        self.fields["manager"].choices = [
            (manager["sys_id"], manager["name"]) for manager in service_now_managers
        ]


class AddAssetForm(GovFormattedForm):
    asset_name = forms.CharField(label="Add asset")


class CorrectionForm(GovFormattedForm):
    CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    is_correct = forms.ChoiceField(
        label="I confirm that all information is up to date and correct",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
    )
    whats_incorrect = forms.CharField(
        required=False,
        label="Please tell us what's wrong",
        widget=forms.Textarea(),
        max_length=1000,
    )


class ReturnOptionForm(GovFormattedForm):
    return_option = forms.ChoiceField(
        label="",
        choices=ReturnOption.choices,
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
    )


class ReturnInformationForm(GovFormattedForm):
    personal_phone = forms.CharField(label="Personal phone", max_length=16)
    contact_email = forms.EmailField(label="Contact email for collection")
    address_building = forms.CharField(
        label="Building and street",
    )
    address_city = forms.CharField(
        label="Town or city",
    )
    address_county = forms.CharField(
        label="County",
    )
    address_postcode = forms.CharField(
        label="Postcode",
    )

    def __init__(self, *args, hide_address: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        address_fields: List[str] = [
            "address_building",
            "address_city",
            "address_county",
            "address_postcode",
        ]
        if hide_address:
            for field_name in address_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()


class PdfFileField(forms.FileField):
    def validate(self, value: UploadedFile) -> None:
        if value.content_type != "application/pdf":
            raise ValidationError("File must be a PDF")
        return super().validate(value)


class LineManagerDetailsForm(GovFormattedForm):
    # TODO: Populate security clearances
    SECURITY_CLEARANCES = [
        ("security_clearance_1", "Security clearance 1"),
    ]
    uksbs_pdf = PdfFileField(
        label="UK SBS PDF",  # /PS-IGNORE
    )
    security_clearance = forms.ChoiceField(
        label="Security clearance",
        choices=SECURITY_CLEARANCES,
    )
    rosa_user = forms.BooleanField(
        label="Is the leaver a ROSA user?",  # /PS-IGNORE
        required=False,
    )
    has_dse = forms.BooleanField(
        label="Does the leaver have any Display Screen Equipment?",
        required=False,
    )
    holds_government_procurement_card = forms.BooleanField(
        label="Does the leaver hold a government procurement card?",
    )
    service_now_reference_number = forms.CharField(
        label="Service Now reference number",
    )
    # TODO: Populate departments
    DEPARTMENT_TRANSFER_CHOICES = [
        ("not_transferring", "Not transferring"),
    ]
    department_transferring_to = forms.ChoiceField(
        label="Department transferring to",
        choices=DEPARTMENT_TRANSFER_CHOICES,
    )
    loan_end_date = forms.DateField(
        label="Loan end date",
    )
