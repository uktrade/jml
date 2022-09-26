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


class RosaKit(TextChoices):
    MOBILE = "mobile", "ROSA Mobile"
    LAPTOP = "laptop", "ROSA Laptop"
    KEY = "key", "ROSA Key"


class RosaKitForm(forms.Form):
    user_has = forms.MultipleChoiceField(
        label="Select the kit that the leaver has",
        help_text="Select all that apply.",
        choices=RosaKit.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    user_returned = forms.MultipleChoiceField(
        label="Select the kit that has been returned",
        help_text="Select all that apply.",
        choices=RosaKit.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-rosa-kit-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkboxes(
                "user_has",
                legend_size=Size.SMALL,
            ),
            Field.checkboxes(
                "user_returned",
                legend_size=Size.SMALL,
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
