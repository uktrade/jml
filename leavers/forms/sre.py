from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Div, Field, Layout, Submit
from django import forms
from django.db.models.enums import TextChoices, Choices
from django.urls import reverse


class ServiceAndToolActions(Choices):
    NOT_STARTED = None, "Not started"
    NOT_APPLICABLE = "not_applicable", "Not applicable"
    REMOVED = "removed", "Removed"


class SREServiceAndToolsForm(forms.Form):
    action = forms.ChoiceField(
        label="",
        choices=ServiceAndToolActions.choices,
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


class SREAddTaskNoteForm(forms.Form):
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


class SREConfirmCompleteForm(forms.Form):
    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "sre-detail", kwargs={"leaving_request_uuid": leaving_request_uuid}
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
