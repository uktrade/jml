from typing import Dict, List, Optional, Union

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fluid, Layout, Submit
from django import forms
from django.http.request import HttpRequest
from django.shortcuts import render

from core.forms import BaseForm


class SearchForm(BaseForm):
    required_error_messages: Dict[str, str] = {
        "search_terms": "Please enter a name or email address.",
    }

    search_terms = forms.CharField(
        label="Search for your line manager by entering their name or email address."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    remove_url: Optional[str] = None,
    pre_html: Optional[HTML] = None,
    field_label: Optional[str] = None,
) -> List[Union[Field, HTML]]:
    """Crispy forms field for an autocomplete field.

    Args:
        form (forms.Form):
            The form the field belongs to.
        request (HttpRequest):
            The request object.
        field_name (str):
            The name of the field.
        search_url (str):
            The URL to the search view.
        remove_text (Optional[str], optional):
            The text to display on the remove button. Defaults to None.
        remove_url (Optional[str], optional):
            The URL to the remove view. Defaults to None.

    Returns:
        List[Union[Field, HTML]]:
            A list of crispy form fields.

    Usage:
        Inside the Form's __init__ method
        ```python
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
        ```
    """

    current_value = form[field_name].value()
    if not current_value:
        current_value = form.initial.get(field_name)

    output = []

    if field_label:
        output.append(
            HTML(
                "<label class='govuk-label'"
                " for='id_{field_name}_search'>"
                "<strong>{field_label}</strong></label>"
            )
        )

    if pre_html:
        output.append(pre_html)

    output.append(Field.text(field_name, field_width=Fluid.TWO_THIRDS))
    output.append(
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
        )
    )

    return output
