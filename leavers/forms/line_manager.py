from typing import TYPE_CHECKING, Any, Dict, List, Optional

from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import (
    HTML,
    Button,
    Div,
    Field,
    Fieldset,
    Layout,
    Size,
    Submit,
)
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.enums import TextChoices
from django.http.request import HttpRequest
from django.urls import reverse

from core.forms import BaseForm
from core.staff_search.forms import staff_search_autocomplete_field
from core.utils.helpers import make_possessive
from core.utils.staff_index import ConsolidatedStaffDocument
from leavers.types import LeavingRequestLineReport

if TYPE_CHECKING:
    from leavers.models import LeavingRequest


class LeaverPaidUnpaid(TextChoices):
    PAID = "paid", "Paid"
    UNPAID = "unpaid", "Unpaid"


class AnnualLeavePaidOrDeducted(TextChoices):
    DEDUCTED = "deducted", "Deducted"
    PAID = "paid", "Paid"
    NO_ANNUAL_LEAVE = "None", "No annual leave"


class FlexiLeavePaidOrDeducted(TextChoices):
    DEDUCTED = "deducted", "Deducted"
    PAID = "paid", "Paid"
    NO_FLEXI_LEAVE = "None", "No flexi leave"


class DaysHours(TextChoices):
    DAYS = "days", "Days"
    HOURS = "hours", "Hours"


class LineManagerDetailsForm(BaseForm):
    required_error_messages: Dict[str, str] = {
        "leaver_paid_unpaid": "Please select whether the leaver is paid or unpaid.",
    }

    leaver_paid_unpaid = forms.ChoiceField(
        label="",
        choices=LeaverPaidUnpaid.choices,
        widget=forms.RadioSelect,
        help_text=(
            "A paid individual is on the UK SBS Payroll, an unpaid individual "
            "is not on the UK SBS Payroll"
        ),
    )
    annual_leave = forms.ChoiceField(
        label="",
        choices=AnnualLeavePaidOrDeducted.choices,
        widget=forms.RadioSelect,
    )
    annual_leave_measurement = forms.ChoiceField(
        label="How is this measured?",
        choices=DaysHours.choices,
        widget=forms.RadioSelect,
        required=False,
    )
    annual_number = forms.CharField(
        label="",
        required=False,
        help_text=(
            "Accepts a decimal value in increments of 0.25 (e.g. 1.25, 2.5, "
            "3.75, 4.0)"
        ),
    )

    flexi_leave = forms.ChoiceField(
        label="",
        choices=FlexiLeavePaidOrDeducted.choices,
        widget=forms.RadioSelect,
    )
    flexi_number = forms.CharField(
        label="",
        required=False,
        help_text=(
            "Accepts a decimal value in increments of 0.25 (e.g. 1.25, 2.5, "
            "3.75, 4.0)"
        ),
    )

    def __init__(
        self,
        leaver_name: str,
        user_is_line_manager: bool,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.fields["leaver_paid_unpaid"].label = f"Is {leaver_name} Paid or Unpaid?"
        self.fields["annual_leave"].label = f"Does {leaver_name} have annual leave to be paid or deducted?"
        self.fields["flexi_leave"].label = f"Does {leaver_name} have any flexi leave to be paid or deducted?"
        self.fields["flexi_leave"].help_text = (
            f"If {leaver_name} has built up any additional flexi leave, "
            "tell us how that leave should be handled."
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("leaver_paid_unpaid", legend_size=Size.MEDIUM),
            Field.radios("annual_leave", legend_size=Size.MEDIUM),
            Div(
                Field.radios("annual_leave_measurement", legend_size=Size.MEDIUM, inline=True),
                css_id="annual_leave_measurement_fieldset",
            ),
            Fieldset(
                "annual_number",
                legend="Number of ??? to be ???",
                legend_size=Size.MEDIUM,
                css_id="annual_number_fieldset",
            ),
            Field.radios("flexi_leave", legend_size=Size.MEDIUM),
            Fieldset(
                "flexi_number",
                legend="Number of hours to be ???",
                legend_size=Size.MEDIUM,
                css_id="flexi_number_fieldset",
            ),
        )

        buttons: List[Button] = []
        if user_is_line_manager:
            buttons.append(Submit("submit", "Next"))
        else:
            buttons.append(Submit("submit", "Save and continue"))
            buttons.append(
                Submit(
                    "save_and_close",
                    "Save and close",
                    css_class="govuk-button--secondary",
                )
            )
        buttons.append(
            Button.warning(
                "cancel_leaving_request",
                "Cancel leaving request",
            )
        )

        self.helper.layout.append(
            Div(
                *buttons,
                css_class="govuk-button-group",
            ),
        )

    def annual_leave_selected(self) -> bool:
        if "annual_leave" not in self.cleaned_data:
            return False

        if self.cleaned_data["annual_leave"] not in [
            AnnualLeavePaidOrDeducted.PAID.value,
            AnnualLeavePaidOrDeducted.DEDUCTED.value,
        ]:
            return False

        return True

    def flexi_leave_selected(self) -> bool:
        if "flexi_leave" not in self.cleaned_data:
            return False

        if self.cleaned_data["flexi_leave"] not in [
            FlexiLeavePaidOrDeducted.PAID.value,
            FlexiLeavePaidOrDeducted.DEDUCTED.value,
        ]:
            return False

        return True

    def clean_annual_leave_measurement(self):
        if self.annual_leave_selected():
            if not self.cleaned_data["annual_leave_measurement"]:
                raise ValidationError(
                    "This field should have a value if there is annual leave "
                    "to be paid or deducted"
                )
        else:
            if self.cleaned_data["annual_leave_measurement"]:
                raise ValidationError(
                    "This field shouldn't have a value if there is no annual leave"
                )

        return self.cleaned_data["annual_leave_measurement"]

    def clean_annual_number(self):
        annual_number: Optional[str] = self.cleaned_data.get("annual_number")
        if self.annual_leave_selected():
            if not annual_number:
                raise ValidationError(
                    "This field should have a value if there is annual leave "
                    "to be paid or deducted"
                )

            try:
                annual_number_float = float(annual_number)
            except ValueError:
                raise ValidationError("This value must be a number")

            if annual_number_float % 0.25 != 0.0:
                raise ValidationError("This value must be given in intervals of .25")

        else:
            if annual_number:
                raise ValidationError(
                    "This field shouldn't have a value if there is no annual leave"
                )
            annual_number = None

        return annual_number

    def clean_flexi_number(self):
        flexi_number: Optional[str] = self.cleaned_data.get("flexi_number")
        if self.flexi_leave_selected():
            if not flexi_number:
                raise ValidationError(
                    "This field should have a value if there is flexi leave "
                    "to be paid or deducted"
                )

            try:
                flexi_number_float = float(flexi_number)
            except ValueError:
                raise ValidationError("This value must be a number")

            if flexi_number_float % 0.25 != 0.0:
                raise ValidationError("This value must be given in intervals of .25")
        else:
            if flexi_number:
                raise ValidationError(
                    "This field shouldn't have a value if there is no flexi leave"
                )
            flexi_number = None

        return flexi_number


class LineReportConfirmationForm(forms.Form):
    def __init__(
        self,
        leaving_request: "LeavingRequest",
        user_is_line_manager,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.leaving_request = leaving_request

        self.helper = FormHelper()
        self.helper.layout = Layout()

        buttons: List[Button] = []
        if user_is_line_manager:
            buttons.append(Submit("submit", "Next"))
        else:
            buttons.append(Submit("submit", "Save and continue"))
            buttons.append(
                Submit(
                    "save_and_close",
                    "Save and close",
                    css_class="govuk-button--secondary",
                )
            )
        buttons.append(
            Button.warning(
                "cancel_leaving_request",
                "Cancel leaving request",
            )
        )

        self.helper.layout.append(
            Div(
                *buttons,
                css_class="govuk-button-group",
            ),
        )

    def clean(self) -> Optional[Dict[str, Any]]:
        # Check that all line reports have a Line Manager selected.
        lr_line_reports: List[LeavingRequestLineReport] = (
            self.leaving_request.line_reports
        )
        for line_report in lr_line_reports:
            if not line_report["line_manager"]:
                self.add_error(
                    None,
                    f"Line report {line_report['name']} has no Line Manager selected.",
                )
        return super().clean()


class LineManagerConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Accept and send"),
        )


class ReasonForLeaving(TextChoices):
    """
    Reason for leaving choices.
    """

    RESIGNATION = "resignation", "Resignation"
    END_OF_CONTRACT = "end_of_contract", "End of contract"


class ConfirmLeavingDate(BaseForm):
    required_error_messages: Dict[str, str] = {
        "data_recipient": "Please select the Google Drive data transfer recipient.",
    }

    last_day = DateInputField(
        label="What is the leaver's last working day?", help_text="For example, 27 3 2007"
    )
    leaving_date = DateInputField(
        label="What is the leaver's leaving date?", help_text="For example, 27 3 2007"
    )
    data_recipient = forms.CharField(label="", widget=forms.HiddenInput)

    def __init__(
        self,
        request: HttpRequest,
        leaving_request_uuid: str,
        leaver: ConsolidatedStaffDocument,
        user_is_line_manager: bool,
        needs_data_transfer: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        leaver_name: str = leaver["first_name"] + " " + leaver["last_name"]
        possessive_leaver_first_name = make_possessive(leaver["first_name"])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                HTML(
                    f"<p class='govuk-body'>This is the last date {leaver_name} "
                    f"will work for {settings.DEPARTMENT_ACRONYM}. After this "
                    "date they will not have access to any of the "
                    f"{settings.DEPARTMENT_ACRONYM}-provided systems and "
                    "buildings.</p>"
                ),
                Field("last_day"),
                legend=f"Confirm {possessive_leaver_first_name} last working day",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    f"<p class='govuk-body'>This is the last date {leaver_name} "
                    "will be employed and paid by "
                    f"{settings.DEPARTMENT_ACRONYM}.</p>"
                ),
                Field("leaving_date"),
                legend=f"Confirm {possessive_leaver_first_name} leaving date",
                legend_size=Size.MEDIUM,
            ),
        )

        if needs_data_transfer:
            self.helper.layout.append(
                *staff_search_autocomplete_field(
                    form=self,
                    request=request,
                    field_name="data_recipient",
                    search_url=reverse(
                        "line-manager-data-recipient-search",
                        kwargs={"leaving_request_uuid": leaving_request_uuid},
                    ),
                    remove_text="Remove data recipient",
                    remove_url=reverse(
                        "line-manager-remove-data-recipient",
                        kwargs={"leaving_request_uuid": leaving_request_uuid},
                    ),
                    pre_html=HTML(
                        f"<p class='govuk-body'>If {leaver_name} has any files in "
                        "Google Drive, tell us who these should be transferred to."
                        "</p>"
                    ),
                    field_label="Google Drive data transfer"
                ),
            )
        else:
            self.fields["data_recipient"].widget = forms.HiddenInput()
            self.fields["data_recipient"].required = False
            self.helper.layout.append(Field("data_recipient"))

        buttons: List[Button] = []
        if user_is_line_manager:
            buttons.append(Submit("submit", "Next"))
        else:
            buttons.append(Submit("submit", "Save and continue"))
            buttons.append(
                Submit(
                    "save_and_close",
                    "Save and close",
                    css_class="govuk-button--secondary",
                )
            )
        buttons.append(
            Button.warning(
                "cancel_leaving_request",
                "Cancel leaving request",
            )
        )

        self.helper.layout.append(
            Div(
                *buttons,
                css_class="govuk-button-group",
            ),
        )


class OfflineServiceNowForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "I have completed the Service Now request"),
        )
