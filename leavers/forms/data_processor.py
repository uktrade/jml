from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fluid, Layout, Submit
from django import forms


class LeavingRequestListingSearchForm(forms.Form):
    query = forms.CharField(
        label="",
        help_text="Search leaver by name or email",
        required=False,
    )

    def __init__(self, full_width: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        if full_width:
            query_field = Field.text("query")
        else:
            query_field = Field.text("query", field_width=Fluid.ONE_QUARTER)

        self.helper.layout = Layout(
            query_field,
            Submit("submit", "Search"),
        )
