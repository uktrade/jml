from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Div, Layout, Submit
from django.urls import reverse

from core.forms import GovFormattedForm


class BuildingPassDestroyedForm(GovFormattedForm):
    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cancel_url = reverse(
            "security-team-building-pass-confirmation",
            args=[leaving_request_uuid],
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Submit(
                    "save",
                    "Confirm building pass destroyed",
                    css_class="govuk-button--warning",
                ),
                HTML(
                    f"<a href='{cancel_url}' class='govuk-button "
                    "govuk-button--secondary'>Cancel</a>"
                ),
                css_class="govuk-button-group",
            ),
        )
