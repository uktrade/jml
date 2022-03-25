from typing import Dict

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms
from django.db.models.enums import TextChoices

from core.forms import GovFormattedForm


class SecurityPassChoices(TextChoices):
    RETURNED = "returned", "Returned"
    DESTROYED = "destroyed", "Destroyed"


class SecurityTeamConfirmCompleteForm(GovFormattedForm):
    security_pass = forms.ChoiceField(
        label="Security pass",
        required=False,
        choices=[(None, "Select an option")] + SecurityPassChoices.choices,  # type: ignore
    )
    rosa_laptop_returned = forms.BooleanField(
        label="ROSA laptop returned",
        required=False,
    )
    rosa_key_returned = forms.BooleanField(
        label="ROSA log-in key returned",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_message_replacement: Dict[str, str] = {
            "security_pass": "Security pass",
            "rosa_laptop_returned": "ROSA laptop returned",
            "rosa_key_returned": "ROSA log-in keyreturned",
        }
        for field_name, field in self.fields.items():
            if field_name in required_message_replacement:
                message_replacement = required_message_replacement[field_name]
                field.error_messages[
                    "required"
                ] = f"Select '{message_replacement}' to confirm removal."

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkbox("security_pass"),
            Field.checkbox("rosa_laptop_returned"),
            Field.checkbox("rosa_key_returned"),
            Submit(
                "save",
                "Save and continue later",
                css_class="govuk-button--secondary",
            ),
            Submit("submit", "Confirm and send"),
        )
