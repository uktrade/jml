import datetime

from django import forms
from django.core.exceptions import ValidationError

from core.forms import GovFormattedForm, GovFormattedModelForm
from leavers.models import LeavingRequest, ReturnOptions
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
        label="VPN access removed?",
        required=True,
    )
    govuk_paas = forms.BooleanField(
        label="GOVUK PAAS access removed?",
        required=True,
    )
    github = forms.BooleanField(
        label="Github user removed from teams and repos?",
        required=False,
    )
    sentry = forms.BooleanField(
        required=False,
    )
    slack = forms.BooleanField(
        required=False,
    )
    sso = forms.BooleanField(
        label="SSO access removed?",
        required=True,
    )
    aws = forms.BooleanField(
        label="AWS access removed?",
        required=True,
    )
    jira = forms.BooleanField(
        label="Jira access removed?",
        required=True,
    )


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
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Last name")
    personal_email = forms.EmailField(label="Email")
    personal_phone = forms.CharField(label="Phone", max_length=16)
    personal_address = forms.CharField(
        label="Address",
        widget=forms.Textarea,
    )
    # Professional details
    grade = forms.CharField(label="Grade")
    job_title = forms.CharField(label="Job title")
    directorate = forms.CharField(label="Directorate")
    department = forms.CharField(label="Department")
    work_email = forms.EmailField(label="Email")
    manager = forms.CharField(label="Manager")
    staff_id = forms.CharField(label="Staff ID")


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
        choices=ReturnOptions.choices,
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
    )


class ReturnInformationForm(GovFormattedForm):
    personal_phone = forms.CharField(label="Personal phone", max_length=16)
    contact_email = forms.EmailField(label="Contact email for collection")
    address = forms.CharField(
        label="Collection Address",
        widget=forms.Textarea,
    )

    def __init__(self, *args, hide_address: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        if hide_address:
            self.fields["address"].required = False
            self.fields["address"].widget = forms.HiddenInput()
