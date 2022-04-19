from typing import List, Literal

from crispy_forms_gds.choices import Choice
from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Field, Fieldset, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices

from core.forms import GovFormattedForm, YesNoField
from core.service_now import get_service_now_interface


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
    pass


class LeaverUpdateForm(GovFormattedForm):
    # Personal details
    first_name = forms.CharField(label="")
    last_name = forms.CharField(label="")
    contact_email_address = forms.EmailField(label="")
    job_title = forms.CharField(label="")
    directorate = forms.ChoiceField(label="", choices=[])
    staff_id = forms.CharField(label="")
    # Extra information
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    locker_number = forms.CharField(label="")
    has_gov_procurement_card = YesNoField(label="")
    has_rosa_kit = YesNoField(label="")
    has_dse = YesNoField(label="")

    leaving_date = DateInputField(
        label="",
    )
    last_day = DateInputField(
        label="",
    )

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
            Fieldset(
                Field("first_name"),
                legend="First name",  # /PS-IGNORE
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("last_name"),
                legend="Last name",  # /PS-IGNORE
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("contact_email_address"),
                legend="Personal email",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("job_title"),
                legend="Job title",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("directorate"),
                legend="Directorate",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("staff_id"),
                legend="Staff ID",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("security_clearance"),
                legend="Security clearance type",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("locker_number"),
                legend="Locker number",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("has_gov_procurement_card", inline=True),
                legend="Do you have a Government Procurement Card?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("has_rosa_kit", inline=True),
                legend="Do you have a ROSA kit?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("has_dse", inline=True),
                legend="Do you have any display screen equipment?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will be employed "
                    "by the department and the last day you will be paid for.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend="Leaving date",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will be working "
                    "at DIT. After this date you will no longer have access to any "
                    "DIT provided systems and buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend="Last working day",
                legend_size=Size.MEDIUM,
            ),
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
