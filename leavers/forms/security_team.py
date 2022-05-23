from typing import Dict

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout, Size, Submit
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
        choices=SecurityPassChoices.choices,
        widget=forms.RadioSelect,
    )
    rosa_laptop_returned = forms.BooleanField(
        label="ROSA laptop",
        required=False,
    )
    rosa_key_returned = forms.BooleanField(
        label="ROSA log-in key",
        required=False,
    )

    def __init__(self, leaver_name: str, completed: bool = False, *args, **kwargs):
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
            Field.radios("security_pass", legend_size=Size.SMALL),
            Fieldset(
                Field.checkbox("rosa_laptop_returned"),
                Field.checkbox("rosa_key_returned"),
                legend="Kit returned",
                legend_size=Size.SMALL,
            ),
        )
        if completed:
            self.helper.layout.append(Submit("save", "Save changes"))
        else:
            self.helper.layout.append(
                HTML(
                    "<p class='govuk-body'>Click the ‘Confirm and send’ button "
                    "only when you have completed all required actions for "
                    f"<em>{leaver_name}</em>.</p>"
                )
            )
            self.helper.layout.append(
                Submit(
                    "save",
                    "Save as draft",
                    css_class="govuk-button--secondary",
                )
            )
            self.helper.layout.append(Submit("submit", "Confirm and send"))
