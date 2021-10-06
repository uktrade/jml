from django import forms
from django.core.exceptions import ValidationError

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

    def clean(self):
        cleaned_data = super().clean()
        for_self = cleaned_data.get("for_self")
        leaver_email_address = cleaned_data.get("leaver_email_address")

        if not for_self and not leaver_email_address:
            raise ValidationError(
                "If you are leaving the DIT, please check the 'I am "
                "leaving DIT' checkbox. If you are filling this form "
                "out for someone else please provide their email "
                "address"
            )
