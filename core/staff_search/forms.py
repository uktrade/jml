from typing import Dict, List, Optional, Union

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fluid, Layout, Submit
from django import forms
from django.http.request import HttpRequest
from django.shortcuts import render


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


def staff_search_autocomplete_field(
    *,
    form: forms.Form,
    request: HttpRequest,
    field_name: str,
    search_url: str,
    remove_text: Optional[str] = None,
    remove_url: Optional[str] = None
) -> List[Union[Field, HTML]]:
    """
    Crispy forms field for an autocomplete field.

    Usage (inside the Form's __init__ method):
    self.helper = FormHelper()
        self.helper.layout = Layout(
            ...
            *staff_search_autocomplete_field(
                form=self,
                request=request,
                field_name="leaver_manager",
                # The StaffSearchView URL
                search_url=reverse("leaver-manager-search"),
                # An optional URL to remove the selected staff member
                remove_url=reverse("leaver-remove-line-manager"),
            ),
            ...
        )
    )
    """

    current_value = form[field_name].value()
    if not current_value:
        current_value = form.initial.get(field_name)

    return [
        Field.text(field_name, css_id="sadsa", field_width=Fluid.TWO_THIRDS),
        HTML(
            render(
                request,
                "staff_search/search_field.html",
                {
                    "search_url": search_url,
                    "search_identifier": field_name,
                    "staff_uuid": current_value,
                    "remove_text": remove_text,
                    "remove_url": remove_url,
                },
            ).content.decode()
        ),
    ]
