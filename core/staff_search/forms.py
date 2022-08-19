from typing import Dict

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms


class SearchForm(forms.Form):
    required_error_messages: Dict[str, str] = {
        "search_terms": "Please enter a name or email address.",
    }

    search_terms = forms.CharField(
        label="Search for your line manager by entering their name or email address."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("search_terms"),
            Submit("submit", "Search"),
        )
