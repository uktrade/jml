from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms

from core.forms import GovFormattedForm


class AssetSearchForm(GovFormattedForm):
    search_terms = forms.CharField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("search_terms"),
            Submit("submit", "Search"),
        )
