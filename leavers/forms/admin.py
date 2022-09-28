from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Layout, Submit
from django import forms
from django.urls import reverse


class ManuallyOffboardedFromUKSBSForm(forms.Form):
    def __init__(self, leaving_request_uuid: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        back_link = reverse(
            "admin-leaving-request-detail",
            kwargs={"leaving_request_id": leaving_request_uuid},
        )
        self.helper.layout = Layout(
            Submit(
                "submit",
                "Mark as manually offboarded from UK SBS",
                css_class="govuk-button--warning",
            ),
            HTML(
                f"<a href='{back_link}' class='govuk-button govuk-button--secondary' "
                "data-module='govuk-button'>Cancel</a>"
            ),
        )
