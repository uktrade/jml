from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Div, Field, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices
from django.urls import reverse


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
                    "Close record",
                    css_class="govuk-button--warning",
                ),
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
