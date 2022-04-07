from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout, Size, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from core.forms import GovFormattedForm, YesNoField
from leavers.forms.leaver import SecurityClearance


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


class LineManagerDetailsForm(GovFormattedForm):
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    holds_government_procurement_card = YesNoField(
        label="",
    )
    rosa_user = YesNoField(
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.select("security_clearance"),
                legend="Security clearance",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>Government procurement card is a "
                    "payment card issued by DIT.</p>"
                ),
                Field.radios(
                    "holds_government_procurement_card",
                    inline=True,
                ),
                legend="Do they have a Government Procurement Card?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>ROSA is a secure IT system platform for "
                    "managing work classified at official, sensitive, secret or top "
                    "secret level.</p>"
                ),
                Field.radios("rosa_user", inline=True),
                legend="Do they have ROSA kit?",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Save and continue"),
        )


class LineManagerConfirmationForm(GovFormattedForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Confirm and send"),
        )


class ConfirmLeavingDate(GovFormattedForm):
    leaving_date = DateInputField(
        label="",
    )
    last_day = DateInputField(
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day the leaver will "
                    "be employed by the department and the last day the leaver will "
                    "be paid for.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend="Leaving date",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day the leaver will "
                    "be working at DIT. After this date the leaver will no longer "
                    "have access to any DIT provided systems and buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend="Last working day",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Save and continue"),
        )
