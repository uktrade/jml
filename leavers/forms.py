import datetime

from django.core.exceptions import ValidationError
from django import forms
from django.forms.widgets import (
    Textarea,
    Select,
    CheckboxInput,
    TextInput,
    EmailInput,
)

from leavers.models import LeavingRequest
from leavers.widgets import DateSelectorWidget


class GovFormattedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.items():
            widget = field[1].widget
            if isinstance(widget, Textarea):
                widget.attrs.update({"class": "govuk-textarea"})
            elif isinstance(widget, Select):
                widget.attrs.update({"class": "govuk-select"})
            elif isinstance(widget, CheckboxInput):
                widget.attrs.update({"class": "govuk-checkboxes__input"})
            elif isinstance(widget, TextInput) or isinstance(widget, EmailInput):
                widget.attrs.update({"class": "govuk-input"})


class GovFormattedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.items():
            widget = field[1].widget
            if isinstance(widget, Textarea):
                widget.attrs.update({"class": "govuk-textarea"})
            elif isinstance(widget, Select):
                widget.attrs.update({"class": "govuk-select"})
            elif isinstance(widget, CheckboxInput):
                widget.attrs.update({"class": "govuk-checkboxes__input"})
            elif isinstance(widget, TextInput) or isinstance(widget, EmailInput):
                widget.attrs.update({"class": "govuk-input"})


class LeaversForm(GovFormattedForm):
    for_self = forms.BooleanField(
        label='I am leaving the DIT (leave blank if filling in for someone else)',
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
        fields = (
            "hardware_received",
        )


class SREConfirmCompleteForm(GovFormattedForm):
    vpn_access = forms.BooleanField(
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
    # slack = forms.BooleanField(
    #     required=False,
    # )
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
        ("me", 'Me'),
        ("someone_else", 'Someone Else'),
    ]

    who_for = forms.ChoiceField(
        choices=CHOICES,
        widget=forms.RadioSelect(
            attrs={"class": "govuk-radios__input"}
        )
    )
    #
    #
    # def clean(self):
    #     cleaned_data = super().clean()
    #     for_self = cleaned_data.get("for_self")
    #     leaver_email_address = cleaned_data.get("leaver_email_address")
    #
    #     if not for_self:
    #         raise ValidationError(
    #             "If you are leaving the DIT, please select the 'me'"
    #             "checkbox. If you are filling this form out"
    #             "for someone else, please select 'Some One Else'"
    #         )


class WhenAreTheyLeavingForm(GovFormattedForm):
    last_day = forms.DateField(
        label="",
        initial=datetime.date.today,
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=True,
    )

