from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fluid, Layout, Submit
from django import forms


class LeavingRequestListingSearchForm(forms.Form):
    query = forms.CharField(
        label="",
        help_text="",
        required=False,
    )

    def __init__(self, full_width: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        field_kwargs = {
            "placeholder": "Search leaver by name or email",
        }

        if not full_width:
            field_kwargs.update(
                field_width=Fluid.ONE_HALF,
            )

        self.query_field = Field.text("query", **field_kwargs)

        self.helper.layout = Layout(
            self.query_field,
            Submit("submit", "Search"),
        )


class HRLeavingRequestListingSearchForm(LeavingRequestListingSearchForm):
    def __init__(self, full_width: bool = False, *args, **kwargs):
        super().__init__(full_width, *args, **kwargs)

        self.fields["query"].help_text = "Find an existing leaving request"

        self.helper.layout = Layout(
            self.query_field,
            Submit("submit", "Search", css_class="govuk-button--secondary"),
        )
