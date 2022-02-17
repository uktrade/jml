from typing import List, Literal

from crispy_forms_gds.choices import Choice
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Field, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices

from core.forms import GovFormattedForm, YesNoField
from core.service_now import get_service_now_interface
from leavers.widgets import DateSelectorWidget


class SecurityClearance(TextChoices):
    """
    Security Clearance levels
    """

    CTC = "ctc", "Counter Terrorist Check"
    SC = "sc", "Security Check"
    ESC = "esc", "Enhanced Security Check"
    DV = "dv", "Developed Vetting"
    EDV = "edv", "Enhanced Developed Vetting"


class LeaverConfirmationForm(GovFormattedForm):
    last_day = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=False,
    )


class LeaverUpdateForm(GovFormattedForm):
    # Personal details
    first_name = forms.CharField(label="First name")  # /PS-IGNORE
    last_name = forms.CharField(label="Last name")  # /PS-IGNORE
    contact_email_address = forms.EmailField(label="Personal email")
    job_title = forms.CharField(label="Job title")
    directorate = forms.ChoiceField(label="Directorate", choices=[])
    staff_id = forms.CharField(label="Staff ID")
    # Extra information
    security_clearance = forms.ChoiceField(
        label="Security clearance type",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    locker_number = forms.CharField(label="Locker number")
    has_gov_procurement_card = YesNoField(
        label="Do you have a Government Procurement Card?"
    )
    has_rosa_kit = YesNoField(label="Do you have a ROSA kit?")
    has_dse = YesNoField(label="Do you have any display screen equipment?")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_now_interface = get_service_now_interface()
        service_now_directorates = service_now_interface.get_directorates()
        if not service_now_directorates:
            raise Exception("No directorates returned from Service Now")

        self.fields["directorate"].choices = [
            (directorate["sys_id"], directorate["name"])
            for directorate in service_now_directorates
        ]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("first_name"),
            Field("last_name"),
            Field("contact_email_address"),
            Field("job_title"),
            Field("directorate"),
            Field("staff_id"),
            Field("security_clearance"),
            Field("locker_number"),
            Field.radios("has_gov_procurement_card", inline=True),
            Field.radios("has_rosa_kit", inline=True),
            Field.radios("has_dse", inline=True),
            Submit("submit", "Save and continue"),
        )


class ReturnOptions(TextChoices):
    OFFICE = "office", "Return at the office"
    HOME = "home", "Collection from home"


RETURN_OPTIONS = [
    Choice(
        ReturnOptions.OFFICE.value,
        ReturnOptions.OFFICE.label,
        hint=(
            "You will need to bring in all your equipment on your last day in the "
            "office and return it to the Cirrus Tech Bar."
        ),
    ),
    Choice(
        ReturnOptions.HOME.value,
        ReturnOptions.HOME.label,
        hint=(
            "We will send you a box to return your laptop, iPhone, chargers and "
            "building security pass. This will be collected by a courier, "
            "instructions will be included in the box"
        ),
    ),
]


class ReturnOptionForm(GovFormattedForm):
    return_option = forms.ChoiceField(
        label="",
        choices=RETURN_OPTIONS,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("return_option"),
            Submit("submit", "Save and continue"),
        )


class ReturnInformationForm(GovFormattedForm):
    personal_phone = forms.CharField(label="Personal phone", max_length=16)
    contact_email = forms.EmailField(label="Contact email for collection")
    address_building = forms.CharField(
        label="Building and street",
    )
    address_city = forms.CharField(
        label="Town or city",
    )
    address_county = forms.CharField(
        label="County",
    )
    address_postcode = forms.CharField(
        label="Postcode",
    )

    def __init__(self, *args, hide_address: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("personal_phone"),
            Field("contact_email"),
            Field("address_building"),
            Field("address_city"),
            Field("address_county"),
            Field("address_postcode"),
            Submit("submit", "Save and continue"),
        )

        address_fields: List[str] = [
            "address_building",
            "address_city",
            "address_county",
            "address_postcode",
        ]
        if hide_address:
            for field_name in address_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()


class AddCirrusAssetForm(GovFormattedForm):
    asset_name = forms.CharField(label="Add asset")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_name"),
            Button.secondary("submit", "Add"),
        )


class AddDisplayScreenEquipmentAssetForm(GovFormattedForm):
    asset_name = forms.CharField(label="Add asset")


class CorrectionForm(GovFormattedForm):
    is_correct = YesNoField(
        label="Is this information correct?",
    )
    whats_incorrect = forms.CharField(
        required=False,
        label="Please tell us what's wrong",
        widget=forms.Textarea(),
        max_length=1000,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "is_correct",
                legend_size=Size.MEDIUM,
                inline=True,
            ),
            Field.textarea("whats_incorrect"),
            HTML.p(
                "If you have made any changes, Service Now may contact you to confirm."
            ),
            Submit("submit", "Submit"),
        )

    def clean_whats_incorrect(self) -> str:
        is_correct: Literal["yes", "no"] = self.cleaned_data["is_correct"]
        whats_incorrect: str = self.cleaned_data["whats_incorrect"]

        if is_correct == "yes":
            whats_incorrect = ""

        elif is_correct == "no":
            if not whats_incorrect:
                raise forms.ValidationError(
                    "Please tell us why the information is incorrect"
                )

        return whats_incorrect


class SubmissionForm(GovFormattedForm):
    pass
