from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Div, Field, Fieldset, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices
from django.urls import reverse

from leavers.forms.leaver import radios_with_conditionals
from leavers.types import SecurityClearance


class AddTaskNoteForm(forms.Form):
    note = forms.CharField(
        label="",
        widget=forms.Textarea,
        help_text="Please do not enter personally identifiable information (PII) here",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.textarea(
                "note",
                rows=5,
            ),
            Submit(
                "save",
                "Add comment",
                css_class="govuk-button--secondary",
            ),
        )


class ClearanceStatus(TextChoices):
    ACTIVE = "active", "Active"
    LAPSED = "lapsed", "Lapsed"
    PAUSED = "paused", "Paused"
    OTHER = "other", "Other"


class SecurityClearanceForm(forms.Form):
    clearance_level = forms.ChoiceField(
        label="",
        choices=SecurityClearance.choices,
    )
    status = forms.ChoiceField(
        label="",
        choices=ClearanceStatus.choices,
        widget=forms.RadioSelect,
    )
    other_value = forms.CharField(
        label="",
        required=False,
    )

    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-building-pass-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field("clearance_level"),
                legend="Security clearance level",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                radios_with_conditionals("status"),
                legend="Clearance status",
                legend_size=Size.MEDIUM,
            ),
            Field(
                "other_value",
                legend_size=Size.MEDIUM,
                css_class="radio-conditional-field conditional-status-other",
            ),
            Div(
                Submit(
                    "submit",
                    "Save",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button govuk-button--secondary' "
                    "data-module='govuk-button'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        other_value = cleaned_data.get("other_value")
        if status == ClearanceStatus.OTHER.value and not other_value:
            self.add_error(
                "other_value",
                "A value must be provided when selecting 'Other'",
            )

        return cleaned_data


class BuildingPassStatus(TextChoices):
    ACTIVE = "active", "Active"
    DEACTIVATED = "deactivated", "Deactivated"


class BuildingPassSteps(TextChoices):
    RETURNED = "returned", "Pass returned"
    DESTROYED = "destroyed", "Pass destroyed"


class BuildingPassForm(forms.Form):
    pass_status = forms.ChoiceField(
        label="Edit pass status",
        choices=BuildingPassStatus.choices,
        widget=forms.RadioSelect,
    )
    next_steps = forms.MultipleChoiceField(
        label="Next steps",
        choices=BuildingPassSteps.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-building-pass-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "pass_status",
                legend_size=Size.MEDIUM,
            ),
            Field.checkboxes(
                "next_steps",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Submit(
                    "submit",
                    "Save",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button govuk-button--secondary' "
                    "data-module='govuk-button'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class BuildingPassCloseRecordForm(forms.Form):
    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-building-pass-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Submit(
                    "save",
                    "Confirm record is complete",
                    css_class="govuk-button--warning",
                ),
            ),
            Div(
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button "
                    "govuk-button--secondary'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class RosaKitActions(TextChoices):
    NOT_STARTED = None, "Not started"
    NOT_APPLICABLE = "not_applicable", "Not applicable"
    RETURNED = "returned", "Returned"


class RosaKitFieldForm(forms.Form):
    action = forms.ChoiceField(
        label="",
        choices=RosaKitActions.choices,
        widget=forms.RadioSelect,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("action"),
            Submit("save", "Save"),
        )


class RosaKit(TextChoices):
    MOBILE = "mobile", "ROSA Mobile"
    LAPTOP = "laptop", "ROSA Laptop"
    KEY = "key", "ROSA Key"


class RosaKitCloseRecordForm(forms.Form):
    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-rosa-kit-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Submit(
                    "save",
                    "Confirm record is complete",
                    css_class="govuk-button--warning",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button "
                    "govuk-button--secondary'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )
