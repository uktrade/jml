from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile  # /PS-IGNORE

from core.forms import GovFormattedForm
from core.service_now import get_service_now_interface
from leavers.widgets import DateSelectorWidget


class PdfFileField(forms.FileField):
    def validate(self, value: UploadedFile) -> None:
        super().validate(value)
        if value.content_type != "application/pdf":
            raise ValidationError("File must be a PDF")


class LineManagerDetailsForm(GovFormattedForm):
    # TODO: Populate security clearances
    SECURITY_CLEARANCES = [
        ("security_clearance_1", "Security clearance 1"),
    ]
    uksbs_pdf = PdfFileField(
        label="UK SBS PDF",  # /PS-IGNORE
    )
    security_clearance = forms.ChoiceField(
        label="Security clearance",
        choices=SECURITY_CLEARANCES,
    )
    rosa_user = forms.BooleanField(
        label="Is the leaver a ROSA user?",  # /PS-IGNORE
        required=False,
    )
    has_dse = forms.BooleanField(
        label="Does the leaver have any Display Screen Equipment?",
        required=False,
    )
    holds_government_procurement_card = forms.BooleanField(
        label="Does the leaver hold a government procurement card?",
        required=False,
    )
    service_now_reference_number = forms.CharField(
        label="Service Now reference number",
    )
    department_transferring_to = forms.ChoiceField(
        label="Department transferring to",
    )
    loan_end_date = forms.DateField(
        label="Loan end date",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_now_interface = get_service_now_interface()
        service_now_departments = service_now_interface.get_departments()
        self.fields["department_transferring_to"].choices = [
            ("not_transferring", "Not transferring"),
        ] + [
            (department["sys_id"], department["name"])
            for department in service_now_departments
        ]


class ConfirmLeavingDate(GovFormattedForm):
    leaving_date = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
    )
