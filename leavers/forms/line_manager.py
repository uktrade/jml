from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout, Size, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models.enums import TextChoices

from core.forms import GovFormattedForm
from core.utils.staff_index import ConsolidatedStaffDocument


class PdfFileField(forms.FileField):
    def validate(self, value: UploadedFile) -> None:
        super().validate(value)
        if value.content_type != "application/pdf":
            raise ValidationError("File must be a PDF")


class UksbsPdfForm(GovFormattedForm):
    uksbs_pdf = PdfFileField(
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "uksbs_pdf",
                legend="Upload the UKSBS PDF",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Submit"),
        )


class PaidOrDeducted(TextChoices):
    DEDUCTED = "deducted", "Deducted"
    PAID = "paid", "Paid"


class DaysHours(TextChoices):
    DAYS = "days", "Days"
    HOURS = "hours", "Hours"


class LineManagerDetailsForm(GovFormattedForm):

    annual_leave = forms.ChoiceField(
        label="",
        choices=PaidOrDeducted.choices + [(None, "No annual leave")],
        widget=forms.RadioSelect,
    )
    annual_leave_measurement = forms.ChoiceField(
        label="",
        choices=DaysHours.choices,
        widget=forms.RadioSelect,
    )
    annual_number = forms.CharField(
        label="",
        required=False,
    )

    flexi_leave = forms.ChoiceField(
        label="",
        choices=PaidOrDeducted.choices + [(None, "No flexi leave")],
        widget=forms.RadioSelect,
    )
    flexi_number = forms.CharField(
        label="",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "annual_leave",
                legend="Is there annual leave to be paid or deducted?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("annual_leave_measurement", inline=True),
                legend="How is this measured?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                "annual_number",
                legend="Number of ??? to be ???",
                legend_size=Size.MEDIUM,
            ),
            HTML("<h2 class='govuk-heading-l'>Flexi leave dates</h2>"),
            Fieldset(
                "flexi_leave",
                legend="Is there flexi leave to be paid or deducted?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                "flexi_number",
                legend="Number of hours to be ???",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Save and continue"),
        )

    def clean_annual_number(self):
        if (
            self.cleaned_data["annual_leave"]
            not in [PaidOrDeducted.PAID.value, PaidOrDeducted.DEDUCTED.value]
            and self.cleaned_data["annual_number"]
        ):
            raise ValidationError(
                "This field shouldn't have a value if there is no annual leave"
            )
        try:
            float(self.cleaned_data["annual_number"])
        except ValueError:
            raise ValidationError("This field must be a number")
        return self.cleaned_data["annual_number"]

    def clean_flexi_number(self):
        if (
            self.cleaned_data["flexi_leave"]
            not in [PaidOrDeducted.PAID.value, PaidOrDeducted.DEDUCTED.value]
            and self.cleaned_data["flexi_number"]
        ):
            raise ValidationError(
                "This field shouldn't have a value if there is no flexi leave"
            )
        try:
            float(self.cleaned_data["flexi_number"])
        except ValueError:
            raise ValidationError("This field must be a number")
        return self.cleaned_data["flexi_number"]


class LineManagerConfirmationForm(GovFormattedForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Confirm and send"),
        )


class ReasonForleaving(TextChoices):
    """
    Reason for leaving choices.
    """

    RESIGNATION = "resignation", "Resignation"
    END_OF_CONTRACT = "end_of_contract", "End of contract"


class ConfirmLeavingDate(GovFormattedForm):
    leaving_date = DateInputField(
        label="",
    )
    last_day = DateInputField(
        label="",
    )
    reason_for_leaving = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=ReasonForleaving.choices,
    )

    def __init__(self, leaver: ConsolidatedStaffDocument, *args, **kwargs):
        super().__init__(*args, **kwargs)

        leaver_name: str = leaver["first_name"] + " " + leaver["last_name"]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day the leaver will "
                    "be employed by the department and the last day they will "
                    "be paid for.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend=f"Leaving date - prepopulated by {leaver_name}",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day the leaver will "
                    "be working at DIT. After this date the leaver will no "
                    "longer have access to any DIT provided systems and "
                    "buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend=f"Last working day - prepopulated by {leaver_name}",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("reason_for_leaving"),
                legend="What's their reason for leaving?",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Save and continue"),
        )
