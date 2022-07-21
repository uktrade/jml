from typing import Dict

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Layout, Submit
from django import forms


class SREConfirmCompleteForm(forms.Form):
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

    def __init__(self, completed: bool = False, *args, **kwargs):
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

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkbox("vpn"),
            Field.checkbox("govuk_paas"),
            Field.checkbox("github"),
            Field.checkbox("sentry"),
            Field.checkbox("slack"),
            Field.checkbox("sso"),
            Field.checkbox("aws"),
            Field.checkbox("jira"),
        )

        if completed:
            self.helper.layout.append(Submit("save", "Save changes"))
        else:
            self.helper.layout.append(
                HTML.p(
                    "Select Confirm and Send only when you have removed access to all "
                    "the tools and services for {{ leaver_name }}."
                )
            )
            self.helper.layout.append(
                Submit(
                    "save",
                    "Save and continue later",
                    css_class="govuk-button--secondary",
                )
            )
            self.helper.layout.append(Submit("submit", "Confirm and send"))
