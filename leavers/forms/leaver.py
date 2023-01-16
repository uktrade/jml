from datetime import timedelta
from typing import Dict, List

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

from core.forms import BaseForm, YesNoField
from core.staff_search.forms import staff_search_autocomplete_field
from core.utils.helpers import make_possessive
from leavers.models import LeavingRequest
from leavers.types import LeavingReason, ReturnOptions, SecurityClearance, StaffType


class SelectLeaverForm(BaseForm):
    leaver_uuid = forms.CharField(label="", widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                *staff_search_autocomplete_field(
                    form=self,
                    request=request,
                    field_name="leaver_uuid",
                    search_url=reverse("leaver-leaver-search"),
                    remove_url=reverse("leaver-select-leaver"),
                    remove_text="Remove",
                ),
                legend="Select a leaver to off-board from DIT",
                legend_size=Size.LARGE,
            ),
            Submit("submit", "Next"),
        )


class LeaverJourneyBaseForm(BaseForm):
    required_error_messages_not_leaver: Dict[str, str] = {}

    def __init__(
        self,
        request: HttpRequest,
        leaving_request: LeavingRequest,
        user_is_leaver: bool,
        *args,
        **kwargs,
    ):
        self.request = request
        self.leaving_request = leaving_request
        self.user_is_leaver = user_is_leaver

        self.helper = FormHelper()
        self.helper.layout = Layout()

        super().__init__(*args, **kwargs)

        # Allow partial submission when saving and closing.
        if "save_and_close" in self.data:
            for field_name in self.fields:
                self.fields[field_name].required = False

        if not self.user_is_leaver:
            for (
                field_name,
                required_message,
            ) in self.required_error_messages_not_leaver.items():
                self.fields[field_name].error_messages["required"] = required_message

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


# Build a new choice list using the TextChoices.
LEAVING_CHOICES: List[Choice] = [
    Choice(
        choice.value,
        choice.label,
    )
    for choice in LeavingReason
]


class WhyAreYouLeavingForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "reason": "Please tell us the reason that you are leaving the department.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "reason": "Please tell us the reason that they are leaving the department."
    }

    reason = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=LEAVING_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.user_is_leaver:
            offboard_someone_else_options: List[LeavingReason] = [
                LeavingReason.DISMISSAL,
                LeavingReason.DEATH_IN_SERVICE,
            ]
            for offboard_someone_else_option in offboard_someone_else_options:
                for choice in self.fields["reason"].choices:
                    if choice[0] == offboard_someone_else_option.value:
                        self.fields["reason"].choices.remove(choice)

        # Add the "or" divider and the "None of the above" option.
        self.fields["reason"].choices[-1].divider = "or"
        self.fields["reason"].choices.append(
            Choice("none_of_the_above", "None of the above")
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            radios_with_conditionals("reason"),
        )
        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class StaffTypeForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "staff_type": "Please tell us your type of employment.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "staff_type": "Please tell us the leaver's type of employment.",
    }

    staff_type = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=StaffType.choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout = Layout(
            Field.radios("staff_type"),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class EmploymentProfileForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "first_name": "Please tell us your first name.",  # /PS-IGNORE
        "last_name": "Please tell us your last name.",  # /PS-IGNORE
        "date_of_birth": "Please tell us your date of birth.",
        "job_title": "Please tell us your job title.",
        "security_clearance": "Please select your security clearance from the list.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "first_name": "Please tell us the leaver's first name.",  # /PS-IGNORE
        "last_name": "Please tell us the leaver's last name.",  # /PS-IGNORE
        "date_of_birth": "Please tell us the leaver's date of birth.",
        "job_title": "Please tell us the leaver's job title.",
        "security_clearance": "Please select the leaver's security clearance from the list.",
    }

    first_name = forms.CharField(label="")
    last_name = forms.CharField(label="")
    date_of_birth = DateInputField(label="")
    job_title = forms.CharField(label="")
    security_clearance = forms.ChoiceField(
        label="",
        choices=(
            [(None, "Select security clearance type")] + SecurityClearance.choices  # type: ignore
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        date_of_birth_html = HTML(
            "<p class='govuk-body'>We need your date of birth to "
            "identify you and complete your offboarding.</p>"
        )
        if not self.user_is_leaver:
            date_of_birth_html = HTML(
                "<p class='govuk-body'>We need the leaver's date of birth to "
                "identify them and complete their offboarding.</p>"
            )

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
                date_of_birth_html,
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
                Field("security_clearance"),
                legend="Security clearance type",
                legend_size=Size.SMALL,
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class FindPersonIDForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "personal_email": "Please enter an email for us to search for.",
    }

    personal_email = forms.EmailField(
        label="Personal email", help_text="We'll only use this to find your details."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.user_is_leaver:
            self.fields["personal_email"].label = "Leaver's personal email"
            self.fields[
                "personal_email"
            ].help_text = "We'll only use this to find the leaver's details."

        cancel_url = reverse(
            "leaver-find-details-help",
            kwargs={"leaving_request_uuid", self.leaving_request.uuid},
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("personal_email"),
            Div(
                Submit("submit", "Continue"),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button govuk-button--secondary' "
                    # Hide the cancel button if the form is unbound (fresh, no data).
                    # Only show the button when a form submission has been attempted.
                    f"style='{'display: none' if not self.is_bound else ''}'"
                    "data-module='govuk-button'>Email address cannot be found</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class LeaverDatesForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "leaving_date": "Please enter the day, month and year of your leaving date.",
        "last_day": "Please enter the day, month and year of your last working day.",
        "leaver_manager": "Please select your line manager.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "leaving_date": "Please enter the day, month and year of the leaver's leaving date.",
        "last_day": "Please enter the day, month and year of the leaver's last working day.",
        "leaver_manager": "Please select the leaver's line manager.",
    }

    leaving_date = DateInputField(label="")
    last_day = DateInputField(label="")
    leaver_manager = forms.CharField(label="", widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        line_manager_legend = "Who is your line manager?"
        line_manager_html = HTML(
            "<p class='govuk-body'>Your line manager will confirm your leaving "
            "date. They are responsible for offboarding you from DIT.</p>"
            "<p class='govuk-body'>Add the person you report to if you do not "
            "know who your line manager is.</p>"
        )

        last_day_legend = "When is your last working day?"
        last_day_html = HTML(
            "<p class='govuk-body'>This is the last day you will work for DIT. "
            "After this day, you will not have access to any DIT systems and buildings.</p>"
        )

        leaving_date_legend = "When is your official leaving day?"
        leaving_date_html = HTML(
            "<p class='govuk-body'>This is the last day you will be employed "
            "and paid by DIT.</p>"
        )
        if not self.user_is_leaver:
            leaver_name = self.leaving_request.get_leaver_name()
            possessive_leaver_name = make_possessive(leaver_name)

            line_manager_legend = f"Who is {possessive_leaver_name} line manager?"
            line_manager_html = HTML(
                f"<p class='govuk-body'>{possessive_leaver_name} line manager will confirm "
                "their leaving date. The line manger is responsible for "
                "offboarding the leaver from DIT.</p>"
            )

            last_day_legend = f"When is {possessive_leaver_name} last working day?"
            last_day_html = HTML(
                f"<p class='govuk-body'>This is the last day that {leaver_name} "
                f"will work for DIT. After this day, {leaver_name} will not have "
                "access to any DIT systems and buildings.</p>"
            )

            leaving_date_legend = (
                f"When is {possessive_leaver_name} official leaving day?"
            )
            leaving_date_html = HTML(
                f"<p class='govuk-body'>This is the last day that {leaver_name} "
                "will be employed and paid by DIT.</p>"
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                line_manager_html,
                *staff_search_autocomplete_field(
                    form=self,
                    request=self.request,
                    field_name="leaver_manager",
                    search_url=reverse(
                        "leaver-manager-search",
                        kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                    ),
                    remove_text="Remove line manager",
                    remove_url=reverse(
                        "leaver-remove-line-manager",
                        kwargs={"leaving_request_uuid": self.leaving_request.uuid},
                    ),
                ),
                legend=line_manager_legend,
                legend_size=Size.SMALL,
            ),
            Fieldset(
                last_day_html,
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("last_day"),
                legend=last_day_legend,
                legend_size=Size.SMALL,
            ),
            Fieldset(
                leaving_date_html,
                HTML("<div class='govuk-hint'>For example, 27 3 2007</div>"),
                Field("leaving_date"),
                legend=leaving_date_legend,
                legend_size=Size.SMALL,
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )

    def clean_leaving_date(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        leaving_date = self.cleaned_data["leaving_date"]
        if (
            "save_and_close" not in self.data
            and self.user_is_leaver
            and yesterday > leaving_date
        ):
            raise forms.ValidationError(
                "Leaving date must be in the future (or today)",
            )
        return leaving_date

    def full_clean(self) -> None:
        super().full_clean()

        last_day = self.cleaned_data.get("last_day")
        leaving_date = self.cleaned_data.get("leaving_date")
        if (
            "save_and_close" not in self.data
            and last_day
            and leaving_date
            and last_day > leaving_date
        ):
            self.add_error(
                "last_day",
                "Last working day must be before or on the same day as the leaving date.",
            )


class LeaverHasAssetsForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "has_gov_procurement_card": "Please tell us if you have a GPC.",
        "has_rosa_kit": "Please tell us if you have ROSA kit.",
        "has_dse": "Please tell us if you have any IT equipment.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "has_gov_procurement_card": "Please tell us if the leaver has a GPC.",
        "has_rosa_kit": "Please tell us if the leaver has ROSA kit.",
        "has_dse": "Please tell us if the leaver has any IT equipment.",
    }

    has_gov_procurement_card = YesNoField(label="")
    has_rosa_kit = YesNoField(label="")
    has_dse = YesNoField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        has_gpc_legned = "Do you have a government procurement card (GPC)?"
        has_rosa_legend = "Do you have ROSA equipment?"
        has_dse_legend = "Do you have any IT equipment?"

        if not self.user_is_leaver:
            leaver_name = self.leaving_request.get_leaver_name()

            has_gpc_legned = (
                f"Does {leaver_name} have a government procurement card (GPC)?"
            )
            has_rosa_legend = f"Does {leaver_name} have ROSA equipment?"
            has_dse_legend = f"Does {leaver_name} have any IT equipment?"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.radios("has_gov_procurement_card", inline=False),
                legend=has_gpc_legned,
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.radios("has_rosa_kit", inline=False),
                legend=has_rosa_legend,
                legend_size=Size.SMALL,
            ),
            Fieldset(
                Field.radios("has_dse", inline=False),
                legend=has_dse_legend,
                legend_size=Size.SMALL,
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class HasCirrusKitForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "has_cirrus_kit": "Please tell us if you have Cirrus equipment.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "has_cirrus_kit": "Please tell us if the leaver has Cirrus equipment.",
    }

    has_cirrus_kit = YesNoField(label="Do you have any Cirrus equipment?")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.user_is_leaver:
            leaver_name = self.leaving_request.get_leaver_name()

            self.fields[
                "has_cirrus_kit"
            ].label = f"Does {leaver_name} have any Cirrus equipment?"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "has_cirrus_kit",
                legend_size=Size.MEDIUM,
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class AddCirrusAssetForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "asset_name": "Please enter a name for the asset you wish to add.",
    }
    asset_name = forms.CharField(label="Name of asset")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("asset_name", field_width=Fluid.TWO_THIRDS),
            Button.secondary("submit", "Add"),
        )


def radios_with_conditionals(*args, **kwargs) -> Field:
    field = Field.radios(*args, **kwargs)
    field.context.update(has_conditionals=True)
    return field


class CirrusReturnFormNoAssets(LeaverJourneyBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout()

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


RETURN_OPTIONS = [
    Choice(
        ReturnOptions.OFFICE.value,
        ReturnOptions.OFFICE.label,
        hint=(
            "On the last working day, return all of the equipment to the Cirrus "
            "tech bar in Old Admiralty Building. Located on the 3rd floor the "
            "tech bar is open from 9am to 5pm."
        ),
    ),
    Choice(
        ReturnOptions.HOME.value,
        ReturnOptions.HOME.label,
        hint=(
            "We will send a box to return the Cirrus kit. This will be "
            "collected by a courier, instructions will be included in the box."
        ),
    ),
]


class CirrusReturnFormWithAssets(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "return_option": "Please select how you would like to return your equipment.",
        "office_personal_phone": "Please tell us your contact phone number.",
        "home_personal_phone": "Please tell us your contact phone number.",
        "office_contact_email": "Please tell us your contact email.",
        "home_contact_email": "Please tell us your contact email.",
        "home_address_line_1": "Please tell us the first line of your address.",
        "home_address_city": "Please tell us your town or city.",
        "home_address_county": "Please tell us your county.",
        "home_address_postcode": "Please tell us your postcode.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "return_option": "Please select how the leaver would like to return their equipment.",
        "office_personal_phone": "Please tell us the leaver's contact phone number.",
        "home_personal_phone": "Please tell us the leaver's contact phone number.",
        "office_contact_email": "Please tell us the leaver's contact email.",
        "home_contact_email": "Please tell us the leaver's contact email.",
        "home_address_line_1": "Please tell us the first line of the leaver's address.",
        "home_address_city": "Please tell us the leaver's town or city.",
        "home_address_county": "Please tell us the leaver's county.",
        "home_address_postcode": "Please tell us the leaver's postcode.",
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

        self.helper = FormHelper()

        return_option_legend = "How would you like to return your Cirrus kit?"

        if not self.user_is_leaver:
            leaver_name = self.leaving_request.get_leaver_name()

            return_option_legend = (
                f"How would {leaver_name} like to return their Cirrus kit?"
            )

        self.helper.layout = Layout(
            Fieldset(
                radios_with_conditionals("return_option"),
                legend=return_option_legend,
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
                Field.text(
                    "home_address_line_1",
                    id="home_address_line_1",
                    field_width=Fluid.TWO_THIRDS,
                ),
                Field.text(
                    "home_address_line_2",
                    id="home_address_line_2",
                    field_width=Fluid.TWO_THIRDS,
                ),
                Field.text(
                    "home_address_city",
                    id="home_address_city",
                    field_width=Fluid.TWO_THIRDS,
                ),
                Field.text(
                    "home_address_county",
                    id="home_address_county",
                    field_width=Fluid.TWO_THIRDS,
                ),
                Field.text(
                    "home_address_postcode",
                    id="home_address_postcode",
                    field_width=Fluid.TWO_THIRDS,
                ),
                legend="Address for courier to pick up the Cirrus kit",
                legend_size=Size.SMALL,
                css_class="radio-conditional-field conditional-return_option-home",
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
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


class AddDisplayScreenEquipmentAssetForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "asset_name": "Please enter a name for the asset you wish to add.",
    }

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


class DisplayScreenEquipmentSubmissionForm(LeaverJourneyBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout()

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class LeaverContactDetailsForm(LeaverJourneyBaseForm):
    required_error_messages: Dict[str, str] = {
        "contact_phone": "Please tell us your personal phone number.",
        "contact_email_address": "Please tell us your personal email address.",
        "contact_address_line_1": "Please tell us the first line of your address.",
        "contact_address_city": "Please tell us your town or city.",
        "contact_address_county": "Please tell us your county.",
        "contact_address_postcode": "Please tell us your postcode.",
    }
    required_error_messages_not_leaver: Dict[str, str] = {
        "contact_phone": "Please tell us the leaver's personal phone number.",
        "contact_email_address": "Please tell us the leaver's personal email address.",
        "contact_address_line_1": "Please tell us the first line of the leaver's address.",
        "contact_address_city": "Please tell us the leaver's town or city.",
        "contact_address_county": "Please tell us the leaver's county.",
        "contact_address_postcode": "Please tell us the leaver's postcode.",
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

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("contact_email_address", field_width=Fluid.TWO_THIRDS),
            Field.text("contact_phone", field_width=Fluid.TWO_THIRDS),
            Field.text(
                "contact_address_line_1",
                id="contact_address_line_1",
                field_width=Fluid.TWO_THIRDS,
            ),
            Field.text(
                "contact_address_line_2",
                id="contact_address_line_2",
                field_width=Fluid.TWO_THIRDS,
            ),
            Field.text(
                "contact_address_city",
                id="contact_address_city",
                field_width=Fluid.TWO_THIRDS,
            ),
            Field.text(
                "contact_address_county",
                id="contact_address_county",
                field_width=Fluid.TWO_THIRDS,
            ),
            Field.text(
                "contact_address_postcode",
                id="contact_address_postcode",
                field_width=Fluid.TWO_THIRDS,
            ),
        )

        if self.user_is_leaver:
            self.helper.layout.append(
                Submit("submit", "Next"),
            )
        else:
            self.helper.layout.append(
                Div(
                    Submit("submit", "Save and continue"),
                    Submit(
                        "save_and_close",
                        "Save and close",
                        css_class="govuk-button--secondary",
                    ),
                    css_class="govuk-button-group",
                ),
            )


class LeaverConfirmationForm(LeaverJourneyBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit("submit", "Accept and send"),
        )
