from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms


class SearchForm(forms.Form):
    search_terms = forms.CharField(
        label="Find the member of staff using their name or email"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("search_terms"),
            Submit("submit", "Search"),
        )
