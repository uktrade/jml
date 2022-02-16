from typing import Dict

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fluid, Layout, Submit
from django import forms

from core.forms import GovFormattedForm


class SRESearchForm(GovFormattedForm):
    query = forms.CharField(
        label="",
        help_text="Search leaver by name or email",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("query", field_width=Fluid.ONE_QUARTER),
            Submit("submit", "Search"),
        )


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
