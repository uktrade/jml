from typing import List, cast

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms


class ChoosePrimaryEmailForm(forms.Form):
    next = forms.CharField(required=False, widget=forms.HiddenInput)
    email_address = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
    )

    def __init__(self, email_addresses: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        email_address_field = cast(forms.ChoiceField, self.fields["email_address"])
        email_address_field.choices = [
            (email_address, email_address) for email_address in email_addresses
        ]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("email_address"),
            Submit("submit", "Save"),
        )
