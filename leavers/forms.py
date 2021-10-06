from django import forms
from leavers.models import LeavingRequest
from leavers.widgets import DateSelectorWidget


class LeaversForm(forms.ModelForm):
    class Meta:
        model = LeavingRequest
        fields = (
            "for_self",
            "leaver_email_address",
            "last_day",
        )
        labels = {
            "for_self": 'I am leaving the DIT (leave blank if filling in for someone else)',
            "leaver_email_address": 'Email address of leaver (if not you)',
            "last_day": "When is the leavers last day?",
        }
        widgets = {
            'last_day': DateSelectorWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['for_self'].widget.attrs.update({'class': "govuk-checkboxes__input"})
        self.fields['leaver_email_address'].widget.attrs.update({'class': "govuk-textarea"})
        self.fields['last_day'].widget.attrs.update({'class': "govuk-textarea"})
