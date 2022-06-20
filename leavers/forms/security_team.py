from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Div, Field, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices
from django.urls import reverse

from core.forms import GovFormattedForm


class BuildingPassDestroyedForm(GovFormattedForm):
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
                    "Confirm building pass destroyed",
                    css_class="govuk-button--warning",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button "
                    "govuk-button--secondary'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class BuildingPassNotReturnedForm(GovFormattedForm):
    notes = forms.CharField(
        label="Additional notes (optional)",
        required=False,
        max_length=1000,
    )

    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-building-pass-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.textarea("notes"),
            Div(
                Submit(
                    "save",
                    "Confirm building pass not returned",
                    css_class="govuk-button--warning",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button "
                    "govuk-button--secondary'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class RosaKit(TextChoices):
    MOBILE = "mobile", "ROSA Mobile"
    LAPTOP = "laptop", "ROSA Laptop"
    KEY = "key", "ROSA Key"


class RosaKitForm(GovFormattedForm):
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
    notes = forms.CharField(
        label="Additional notes (optional)",
        required=False,
        max_length=1000,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkboxes(
                "user_has",
                legend_size=Size.LARGE,
            ),
            Field.checkboxes(
                "user_returned",
                legend_size=Size.LARGE,
            ),
            Field.textarea(
                "notes",
                label_size=Size.MEDIUM,
                rows=3,
            ),
            Div(
                Submit(
                    "save",
                    "Save",
                ),
                Submit(
                    "close",
                    "Close record",
                    css_class="govuk-button--warning",
                ),
                css_class="govuk-button-group",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        user_has = cleaned_data["user_has"]
        user_returned = cleaned_data["user_returned"]

        if "save" in self.data:
            return cleaned_data

        # Validation for closing the record
        if RosaKit.MOBILE.value in user_has:
            if RosaKit.MOBILE.value not in user_returned:
                raise forms.ValidationError(
                    {
                        "user_returned": (
                            "User has a ROSA mobile, but it isn't marked "
                            "as returned."
                        )
                    }
                )
        if RosaKit.LAPTOP.value in user_has:
            if RosaKit.LAPTOP.value not in user_returned:
                raise forms.ValidationError(
                    {
                        "user_returned": (
                            "User has a ROSA laptop, but it isn't marked "
                            "as returned."
                        )
                    }
                )
        if RosaKit.KEY.value in user_has:
            if RosaKit.KEY.value not in user_returned:
                raise forms.ValidationError(
                    {
                        "user_returned": (
                            "User has a ROSA Key, but it isn't marked as returned."
                        )
                    }
                )
        if user_has != user_returned:
            raise forms.ValidationError(
                {
                    "user_returned": (
                        "There is a mismatch between the kit the user has "
                        "and the kit that has been returned."
                    )
                }
            )

        return cleaned_data


class RosaKitCloseRecordForm(GovFormattedForm):
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
