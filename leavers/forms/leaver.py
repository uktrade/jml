from datetime import timedelta
from typing import Dict

from crispy_forms_gds.choices import Choice
from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import (
    HTML,
    Button,
    Div,
    Field,
    Fieldset,
    Fluid,
    Layout,
    Size,
    Submit,
)
from django import forms
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils import timezone

from core.forms import YesNoField
from core.staff_search.forms import staff_search_autocomplete_field
from leavers.types import LeavingReason, ReturnOptions, SecurityClearance, StaffType


class LeaverConfirmationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Accept and send"),
        )


# Build a new choice list using the TextChoices.
LEAVING_CHOICES = [
    Choice(
        choice.value,
        choice.label,
    )
    for choice in LeavingReason
]
# Add the "or" divider and the "None of the above" option.
LEAVING_CHOICES[-1].divider = "or"
LEAVING_CHOICES.append(Choice("none_of_the_above", "None of the above"))


class WhyAreYouLeavingForm(forms.Form):
    reason = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=LEAVING_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("reason"),
            Submit("submit", "next"),
        )


class StaffTypeForm(forms.Form):
    staff_type = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=StaffType.choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("staff_type"),
            Submit("submit", "Next"),
        )


class EmploymentProfileForm(forms.Form):
    required_error_messages: Dict[str, str] = {
        "first_name": "Please tell us your first name.",  # /PS-IGNORE
        "last_name": "Please tell us your last name.",  # /PS-IGNORE
        "date_of_birth": "Please tell us your date of birth.",
        "job_title": "Please tell us your job title.",
        "staff_type": "Please select your staff type.",
        "security_clearance": "Please select your security clearance from the list.",
    }

    first_name = forms.CharField(label="")
    last_name = forms.CharField(label="")
    date_of_birth = DateInputField(label="")
    job_title = forms.CharField(label="")
    staff_type = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=StaffType.choices,
    )
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.text("first_name", field_width=Fluid.TWO_THIRDS),
                legend="First name",  # /PS-IGNORE
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.text("last_name", field_width=Fluid.TWO_THIRDS),
                legend="Last name",  # /PS-IGNORE
                legend_size=Size.SMALL,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>We need your date of birth to "
                    "identify you and complete your offboarding.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("date_of_birth"),
                legend="Date of birth",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.text("job_title", field_width=Fluid.TWO_THIRDS),
                legend="Job title",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.radios("staff_type"),
                legend="What staff type are you?",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field("security_clearance"),
                legend="Security clearance type",
                legend_size=Size.SMALL,
            ),
            Submit("submit", "Next"),
        )


class FindPersonIDForm(forms.Form):
    personal_email = forms.EmailField(label="Personal email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse("leaver-find-details-help")

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("personal_email"),
            Div(
                Submit("submit", "Search"),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button govuk-button--secondary' "
                    "data-module='govuk-button'>My email address cannot be found</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


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


class LeaverDatesForm(forms.Form):
    required_error_messages: Dict[str, str] = {
        "leaving_date": "Please enter the day, month and year of your leaving date.",
        "last_day": "Please enter the day, month and year of your last working day.",
        "leaver_manager": "Please select your line manager.",
    }

    leaving_date = DateInputField(label="")
    last_day = DateInputField(label="")
    leaver_manager = forms.CharField(label="", widget=forms.HiddenInput)

    def __init__(self, request: HttpRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                HTML(
                    "<p class='govuk-body'>Your line manager will confirm "
                    "your leaving date. They are responsible for offboarding "
                    "you from DIT.</p>"
                    "<p class='govuk-body'>Add the person you report to if "
                    "you do not know who your line manager is.</p>"
                ),
                *staff_search_autocomplete_field(
                    form=self,
                    request=request,
                    field_name="leaver_manager",
                    search_url=reverse("leaver-manager-search"),
                    remove_text="Remove line manager",
                    remove_url=reverse("leaver-remove-line-manager"),
                ),
                legend="Who is your line manager?",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will work "
                    "for DIT. After this day, you will not have access to any "
                    "DIT systems and buildings.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend="When is your last working day?",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-body'>This is the last day you will be "
                    "employed and paid by DIT.</p>"
                ),
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend="When is your official leaving day?",
                legend_size=Size.SMALL,
            ),
            Submit("submit", "Next"),
        )

    def clean_leaving_date(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        leaving_date = self.cleaned_data["leaving_date"]
        if yesterday > leaving_date:
            raise forms.ValidationError(
                "Leaving date must be in the future (or today)",
            )
        return leaving_date

    def full_clean(self) -> None:
        super().full_clean()

        last_day = self.cleaned_data.get("last_day")
        leaving_date = self.cleaned_data.get("leaving_date")
        if last_day and leaving_date and last_day > leaving_date:
            self.add_error(
                "last_day",
                "Last working day must be before or on the same day as your leaving date.",
            )


class LeaverHasAssetsForm(forms.Form):
    required_error_messages: Dict[str, str] = {
        "has_gov_procurement_card": "Please tell us if you have a GPC.",
        "has_rosa_kit": "Please tell us if you have ROSA kit.",
        "has_dse": "Please tell us if you have any IT equipment.",
    }

    has_gov_procurement_card = YesNoField(label="")
    has_rosa_kit = YesNoField(label="")
    has_dse = YesNoField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.radios("has_gov_procurement_card", inline=False),
                legend="Do you have a government procurement card (GPC)?",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.radios("has_rosa_kit", inline=False),
                legend="Do you have ROSA equipment?",
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.radios("has_dse", inline=False),
                legend="Do you have any IT equipment?",
                legend_size=Size.SMALL,
            ),
            Submit("submit", "Next"),
        )


class HasCirrusKitForm(forms.Form):
    has_cirrus_kit = YesNoField(label="Do you have any Cirrus equipment?")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "has_cirrus_kit",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Next"),
        )


class AddCirrusAssetForm(forms.Form):
    asset_name = forms.CharField(label="Name of asset")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_name", field_width=Fluid.TWO_THIRDS),
            Button.secondary("submit", "Add"),
        )


RETURN_OPTIONS = [
    Choice(
        ReturnOptions.OFFICE.value,
        ReturnOptions.OFFICE.label,
        hint=(
            "On your last working day, return your Cirrus kit to OAB's Tech "
            "Bar (on the 3rd floor). The Tech Bar is open Monday to Friday "
            "from 10am to 4pm."
        ),
    ),
    Choice(
        ReturnOptions.HOME.value,
        ReturnOptions.HOME.label,
        hint=(
            "We will send you a box with instructions to pack your Cirrus kit. "
            "Your box will be collected by courier."
        ),
    ),
]


def radios_with_conditionals(*args, **kwargs) -> Field:
    field = Field.radios(*args, **kwargs)
    field.context.update(has_conditionals=True)
    return field


class CirrusReturnFormNoAssets(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Next"),
        )


class CirrusReturnFormWithAssets(forms.Form):
    required_error_messages: Dict[str, str] = {
        "office_personal_phone": "Please tell us your contact phone number.",
        "home_personal_phone": "Please tell us your contact phone number.",
        "office_contact_email": "Please tell us your contact email.",
        "home_contact_email": "Please tell us your contact email.",
        "home_address_line_1": "Please tell us the first line of your address.",
        "home_address_city": "Please tell us your town or city.",
        "home_address_county": "Please tell us your county.",
        "home_address_postcode": "Please tell us your postcode.",
    }
    return_option = forms.ChoiceField(
        label="",
        choices=RETURN_OPTIONS,
        widget=forms.RadioSelect,
    )

    office_personal_phone = forms.CharField(label="", max_length=16, required=False)
    office_contact_email = forms.EmailField(label="", required=False)

    home_personal_phone = forms.CharField(label="", max_length=16, required=False)
    home_contact_email = forms.EmailField(label="", required=False)

    home_address_line_1 = forms.CharField(label="Address line 1", required=False)
    home_address_line_2 = forms.CharField(label="Address line 2", required=False)
    home_address_city = forms.CharField(label="Town or city", required=False)
    home_address_county = forms.CharField(label="County", required=False)
    home_address_postcode = forms.CharField(label="Postcode", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                radios_with_conditionals("return_option"),
                legend="How would you like to return your Cirrus kit?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                Field.text("office_personal_phone", field_width=Fluid.TWO_THIRDS),
                legend="Contact phone",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-office",
            ),
            Fieldset(
                Field.text("office_contact_email", field_width=Fluid.TWO_THIRDS),
                legend="Contact email",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-office",
            ),
            Fieldset(
                Field.text("home_personal_phone", field_width=Fluid.TWO_THIRDS),
                legend="Contact phone",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-home",
            ),
            Fieldset(
                Field.text("home_contact_email", field_width=Fluid.TWO_THIRDS),
                legend="Contact email",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-home",
            ),
            Fieldset(
                Field.text("home_address_line_1", field_width=Fluid.TWO_THIRDS),
                Field.text("home_address_line_2", field_width=Fluid.TWO_THIRDS),
                Field.text("home_address_city", field_width=Fluid.TWO_THIRDS),
                Field.text("home_address_county", field_width=Fluid.TWO_THIRDS),
                Field.text("home_address_postcode", field_width=Fluid.TWO_THIRDS),
                legend="Address for courier to pick up your Cirrus kit",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-home",
            ),
            Submit("submit", "Next"),
        )

    def full_clean(self) -> None:
        super().full_clean()

        required_fields_mapping = {
            ReturnOptions.OFFICE.value: [
                "office_personal_phone",
                "office_contact_email",
            ],
            ReturnOptions.HOME.value: [
                "home_personal_phone",
                "home_contact_email",
                "home_address_line_1",
                "home_address_city",
                "home_address_county",
                "home_address_postcode",
            ],
        }

        for return_option, return_option_fields in required_fields_mapping.items():
            for return_option_field in return_option_fields:
                if self.cleaned_data.get("return_option") == return_option:
                    required_error_message = self.fields[
                        return_option_field
                    ].error_messages["required"]
                    if not self.cleaned_data.get(return_option_field):
                        self.add_error(return_option_field, required_error_message)
                else:
                    self.cleaned_data.pop(return_option_field, None)


class AddDisplayScreenEquipmentAssetForm(forms.Form):
    asset_name = forms.CharField(label="Asset name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_name", field_width=Fluid.TWO_THIRDS),
            Submit(
                "submit",
                "Add",
                css_class="govuk-button--secondary",
            ),
        )


class SubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Next"),
        )


class LeaverContactDetailsForm(forms.Form):
    required_error_messages: Dict[str, str] = {
        "contact_phone": "Please tell us your personal phone number.",
        "contact_email_address": "Please tell us your personal email address.",
        "contact_address_line_1": "Please tell us the first line of your address.",
        "contact_address_city": "Please tell us your town or city.",
        "contact_address_county": "Please tell us your county.",
        "contact_address_postcode": "Please tell us your postcode.",
    }

    contact_phone = forms.CharField(label="Personal phone number")
    contact_email_address = forms.EmailField(label="Personal email address")
    contact_address_line_1 = forms.CharField(label="Address line 1")
    contact_address_line_2 = forms.CharField(
        label="Address line 2 (optional)", required=False
    )
    contact_address_city = forms.CharField(label="Town or city")
    contact_address_county = forms.CharField(label="County")
    contact_address_postcode = forms.CharField(label="Postcode")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("contact_email_address", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_phone", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_address_line_1", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_address_line_2", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_address_city", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_address_county", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_address_postcode", field_width=Fluid.TWO_THIRDS),
            Submit("submit", "Next"),
        )
