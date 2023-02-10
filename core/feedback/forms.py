from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout, Size, Submit
from django.forms import HiddenInput, ModelForm, RadioSelect

from core.feedback.models import BetaServiceFeedback, SatisfactionOptions


class BetaFeedbackForm(ModelForm):
    class Meta:
        model = BetaServiceFeedback
        fields = ["satisfaction", "comment", "submitter"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["submitter"].widget = HiddenInput()
        self.fields["satisfaction"].label = ""
        self.fields["satisfaction"].required = True
        self.fields["satisfaction"].widget = RadioSelect()
        self.fields["satisfaction"].choices = SatisfactionOptions.choices
        self.fields["comment"].label = ""
        self.fields["comment"].required = True

        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field("submitter"),
            Fieldset(
                Field.radios(
                    "satisfaction",
                    template="widgets/star_rating/star_rating.html",
                ),
                legend="Overall, how did you feel about the service you received today?",
                legend_size=Size.MEDIUM,
            ),
            Fieldset(
                HTML(
                    "<p class='govuk-hint'>Do not include any personal or "
                    "financial information, for example your National "
                    "Insurance or credit card numbers.</p>"
                ),
                Field("comment"),
                legend="How could we improve this service?",
                legend_size=Size.MEDIUM,
            ),
            Submit("submit", "Send feedback"),
        )
