from typing import List, Literal, Optional

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


class StaffType(TextChoices):
    CIVIL_SERVANT = "civil_servant", "Civil servant"
    FAST_STREAMERS = "fast_streamers", "Fast streamers"
    CONTRACTOR = "contractor", "Contractor such as Green Park"
    BENCH_CONTRACTOR = "bench_contractor", "Bench contractor such as Profusion"


class LeaverUpdateForm(GovFormattedForm):
    # Personal details
    first_name = forms.CharField(label="")
    last_name = forms.CharField(label="")
    contact_email_address = forms.EmailField(label="")
    job_title = forms.CharField(label="")
    directorate = forms.ChoiceField(label="", choices=[])
    # Extra information
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    locker_number = forms.CharField(label="", required=False)
    staff_type = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=StaffType.choices,
    )
    has_gov_procurement_card = YesNoField(label="")
    has_rosa_kit = YesNoField(label="")
    has_dse = YesNoField(label="")

    leaving_date = DateInputField(label="")
    last_day = DateInputField(label="")

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
                Field("job_title"),
                legend="Job title",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>Please provide an email address where "
                    "we can contact you after your last working day. We will "
                    "only do this to send you information about your leaving the "
                    "department.</p>"
                ),
                Field("contact_email_address"),
                legend="Contact email",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>Security guidance: this only applies "
                    "if you have security clearance above level Baseline "
                    "Personnel Security Standard (BPSS).</p>"
                ),
                Field("security_clearance"),
                legend="Security clearance type",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("locker_number"),
                legend="Locker number if applicable",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("staff_type"),
                legend="What staff type are you?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>A government procurement card is a "
                    "payment card issued by DIT.</p>"
                ),
                Field.radios("has_gov_procurement_card", inline=True),
                legend="Do you have a government procurement card?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>ROSA is a secure IT system platform "
                    "for managing work classified at official, sensitive, "
                    "secret or top secret level.</p>"
                ),
                Field.radios("has_rosa_kit", inline=True),
                legend="Do you have a ROSA kit?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("has_dse", inline=True),
                legend="Do you have any IT equipment?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will be "
                    "employed by the department and the last day you will "
                    "be paid for.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend="Leaving date",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will be "
                    "working at DIT. After this date you will no longer have "
                    "access to any DIT provided systems and buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend="Last working day",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Save and continue"),
            # TO DELETE?
            Fieldset(
                Field("directorate"),
                legend="Directorate",
                legend_size=Size.MEDIUM,
            ),
        )


class ReturnOptions(TextChoices):
    OFFICE = "office", "Return to the office"
    HOME = "home", "Home collection"


RETURN_OPTIONS = [
    Choice(
        ReturnOptions.OFFICE.value,
        ReturnOptions.OFFICE.label,
        hint=(
            "On your last working day, return all your equipment to the Cirrus "
            "tech bar in Old Admiralty Building. Located on the 3rd floor the "
            "tech bar is open from 9am to 5pm."
        ),
    ),
    Choice(
        ReturnOptions.HOME.value,
        ReturnOptions.HOME.label,
        hint=(
            "We will send you a box to return your cirrus kit. This will be "
            "collected by a courier, instructions will be included in the box."
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
    personal_phone = forms.CharField(label="Contact phone", max_length=16)
    contact_email = forms.EmailField(label="Contact email")
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
            Field("address_building"),
            Field("address_city"),
            Field("address_county"),
            Field("address_postcode"),
            Field("personal_phone"),
            Field("contact_email"),
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
            Submit("submit", "Save and continue"),
        )

    def clean_whats_incorrect(self) -> str:
        whats_incorrect: Optional[str] = self.cleaned_data.get("whats_incorrect")

        is_correct: Optional[Literal["yes", "no"]] = self.cleaned_data.get("is_correct")

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
