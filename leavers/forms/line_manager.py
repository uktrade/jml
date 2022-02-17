from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from core.forms import GovFormattedForm, YesNoField
from leavers.forms.leaver import SecurityClearance
from leavers.widgets import DateSelectorWidget


class PdfFileField(forms.FileField):
    def validate(self, value: UploadedFile) -> None:
        super().validate(value)
        if value.content_type != "application/pdf":
            raise ValidationError("File must be a PDF")


class UksbsPdfForm(GovFormattedForm):
    uksbs_pdf = PdfFileField(
        label="Upload the UKSBS PDF",
    )


class LineManagerDetailsForm(GovFormattedForm):
    security_clearance = forms.ChoiceField(
        label="Security clearance",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    holds_government_procurement_card = YesNoField(
        label="Do they have a Government Procurement Card?",
    )
    rosa_user = YesNoField(
        label="Do they have ROSA kit?",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("security_clearance"),
            Field.radios("holds_government_procurement_card", inline=True),
            Field.radios("rosa_user", inline=True),
            Submit("submit", "Save and continue"),
        )


class ConfirmLeavingDate(GovFormattedForm):
    leaving_date = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
    )
