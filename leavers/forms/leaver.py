from typing import List, Literal, Optional

from crispy_forms_gds.choices import Choice
from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Field, Fieldset, Layout, Size, Submit
from django import forms
from django.db.models.enums import TextChoices

from core.forms import YesNoField
from core.service_now import get_service_now_interface


class SecurityClearance(TextChoices):
    """
    Security Clearance levels
    """

    BPSS = "bpss", "Baseline Personnel Security Standard (BPSS)"
    CTC = "ctc", "Counter Terrorist Check (CTC)"
    SC = "sc", "Security Check (SC)"
    ESC = "esc", "Enhanced Security Check (eSC)"
    DV = "dv", "Developed Vetting (DV)"
    EDV = "edv", "Enhanced Developed Vetting (eDV)"


class LeaverConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Accept and send"),
        )


class StaffType(TextChoices):
    CIVIL_SERVANT = "civil_servant", "Civil servant"
    FAST_STREAMERS = "fast_streamers", "Fast streamers"
    CONTRACTOR = "contractor", "Contractor such as Green Park"
    BENCH_CONTRACTOR = "bench_contractor", "Bench contractor such as Profusion"


class LeaverUpdateForm(forms.Form):
    # Personal details
    first_name = forms.CharField(label="")
    last_name = forms.CharField(label="")
    date_of_birth = DateInputField(label="")
    contact_email_address = forms.EmailField(label="")
    contact_phone = forms.CharField(label="")
    contact_address_line_1 = forms.CharField(label="Address line 1")
    contact_address_line_2 = forms.CharField(label="Address line 2")
    contact_address_city = forms.CharField(label="Town or city")
    contact_address_county = forms.CharField(label="County")
    contact_address_postcode = forms.CharField(label="Postcode")
    job_title = forms.CharField(label="")
    directorate = forms.ChoiceField(label="", choices=[])
    # Extra information
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )
    has_locker = YesNoField(label="")
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

        self.fields["directorate"].choices = [(None, "Select your directorate")] + [
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
                Field("security_clearance"),
                legend="Security clearance type",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>In order to correctly identify "
                    "you, the administrators of security clearance "
                    "require your date of birth.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("date_of_birth"),
                legend="Date of birth",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("directorate"),
                legend="Directorate",
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
                Field("contact_phone"),
                legend="Contact phone",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field("contact_address_line_1"),
                Field("contact_address_line_2"),
                Field("contact_address_city"),
                Field("contact_address_county"),
                Field("contact_address_postcode"),
                legend="Contact address",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.radios("has_locker", inline=True),
                legend="Do you have a locker?",
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
                    "working at DIT. After this date you will no longer have "
                    "access to any DIT provided systems and buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend="Last working day",
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
            Submit("submit", "Save and continue"),
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
            "We will send you a box to return your Cirrus kit. This will be "
            "collected by a courier, instructions will be included in the box."
        ),
    ),
]


class ReturnOptionForm(forms.Form):
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


class ReturnInformationForm(forms.Form):
    personal_phone = forms.CharField(label="", max_length=16)
    contact_email = forms.EmailField(label="")
    address_line_1 = forms.CharField(label="Address line 1")
    address_line_2 = forms.CharField(label="Address line 2")
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
            Fieldset(
                Field("address_line_1"),
                Field("address_line_2"),
                Field("address_city"),
                Field("address_county"),
                Field("address_postcode"),
                legend="Contact address",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field("personal_phone"),
                legend="Contact phone",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field("contact_email"),
                legend="Contact email",
                legend_size=Size.SMALL,
            ),
            Submit("submit", "Save and continue"),
        )

        address_fields: List[str] = [
            "address_line_1",
            "address_line_2",
            "address_city",
            "address_county",
            "address_postcode",
        ]
        if hide_address:
            for field_name in address_fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()


class HasCirrusKitForm(forms.Form):
    has_cirrus_kit = YesNoField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "has_cirrus_kit",
                legend_size=Size.MEDIUM,
                inline=True,
            ),
            Submit("submit", "Continue"),
        )


class AddCirrusAssetForm(forms.Form):
    asset_name = forms.CharField(label="Add asset")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_name"),
            Button.secondary("submit", "Add"),
        )


class AddDisplayScreenEquipmentAssetForm(forms.Form):
    asset_name = forms.CharField(label="Asset name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("asset_name"),
            Submit(
                "submit",
                "Add asset",
                css_class="govuk-button--secondary",
            ),
        )


class CorrectionForm(forms.Form):
    is_correct = YesNoField(
        label="Is this information correct?",
    )
    whats_incorrect = forms.CharField(
        required=False,
        label="If no, please use the text box to provide further information",
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
        whats_incorrect: str = self.cleaned_data.get("whats_incorrect", "")

        is_correct: Optional[Literal["yes", "no"]] = self.cleaned_data.get("is_correct")

        if is_correct == "yes":
            whats_incorrect = ""

        elif is_correct == "no":
            if not whats_incorrect:
                raise forms.ValidationError(
                    "Please tell us why the information is incorrect"
                )

        return whats_incorrect


class SubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Save and continue"),
        )
