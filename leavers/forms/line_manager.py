from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from core.forms import GovFormattedForm, YesNoField
from leavers.models import SecurityClearance
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
        label="Leaver's security clearance",
        choices=SecurityClearance.choices,
    )
    rosa_user = YesNoField(
        label="Is the leaver a ROSA user?",
    )
    holds_government_procurement_card = YesNoField(
        label="Does the leaver hold a government procurement card?",
    )


class ConfirmLeavingDate(GovFormattedForm):
    leaving_date = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
    )
