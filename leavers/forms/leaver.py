from typing import List

from django import forms

from core.forms import GovFormattedForm, YesNoField
from core.service_now import get_service_now_interface
from leavers.models import ReturnOption
from leavers.widgets import DateSelectorWidget


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
    contact_email_address = forms.EmailField(label="Email")
    contact_phone = forms.CharField(label="Phone", max_length=16)
    contact_address = forms.CharField(
        label="Address",
        widget=forms.Textarea,
    )
    # Professional details
    grade = forms.CharField(label="Grade")
    job_title = forms.CharField(label="Job title")
    directorate = forms.ChoiceField(label="Directorate", choices=[])
    department = forms.ChoiceField(label="Department", choices=[])
    email_address = forms.EmailField(label="Email")
    staff_id = forms.CharField(label="Staff ID")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_now_interface = get_service_now_interface()
        service_now_directorates = service_now_interface.get_directorates()
        if not service_now_directorates:
            raise Exception("No directorates returned from Service Now")
        service_now_departments = service_now_interface.get_departments()
        if not service_now_departments:
            raise Exception("No departments returned from Service Now")

        self.fields["directorate"].choices = [
            (directorate["sys_id"], directorate["name"])
            for directorate in service_now_directorates
        ]
        self.fields["department"].choices = [
            (department["sys_id"], department["name"])
            for department in service_now_departments
        ]


class ReturnOptionForm(GovFormattedForm):
    return_option = forms.ChoiceField(
        label="",
        choices=ReturnOption.choices,
        widget=forms.RadioSelect,
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


class AddAssetForm(GovFormattedForm):
    asset_name = forms.CharField(label="Add asset")


class CorrectionForm(GovFormattedForm):
    is_correct = YesNoField(
        label="I confirm that all information is up to date and correct",
    )
    whats_incorrect = forms.CharField(
        required=False,
        label="Please tell us what's wrong",
        widget=forms.Textarea(),
        max_length=1000,
    )
