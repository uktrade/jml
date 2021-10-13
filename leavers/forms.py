import datetime

from django.core.exceptions import ValidationError
from django import forms
from django.forms.widgets import (
    Textarea,
    Select,
    CheckboxInput,
    TextInput,
    EmailInput,
)

from leavers.models import LeavingRequest
from leavers.widgets import DateSelectorWidget


class GovFormattedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.items():
            widget = field[1].widget
            if isinstance(widget, Textarea):
                widget.attrs.update({"class": "govuk-textarea"})
            elif isinstance(widget, Select):
                widget.attrs.update({"class": "govuk-select"})
            elif isinstance(widget, CheckboxInput):
                widget.attrs.update({"class": "govuk-checkboxes__input"})
            elif isinstance(widget, TextInput) or isinstance(widget, EmailInput):
                widget.attrs.update({"class": "govuk-input"})


class GovFormattedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.items():
            widget = field[1].widget
            if isinstance(widget, Textarea):
                widget.attrs.update({"class": "govuk-textarea"})
            elif isinstance(widget, Select):
                widget.attrs.update({"class": "govuk-select"})
            elif isinstance(widget, CheckboxInput):
                widget.attrs.update({"class": "govuk-checkboxes__input"})
            elif isinstance(widget, TextInput) or isinstance(widget, EmailInput):
                widget.attrs.update({"class": "govuk-input"})


class LeaversForm(GovFormattedForm):
    for_self = forms.BooleanField(
        label='I am leaving the DIT (leave blank if filling in for someone else)',
        required=False,
    )
    leaver_email_address = forms.EmailField(
        label="Email address of leaver (if not you)",
        required=False,
    )
    last_day = forms.DateField(
        label="When is the leavers last day?",
        initial=datetime.date.today,
        widget=DateSelectorWidget(),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        for_self = cleaned_data.get("for_self")
        leaver_email_address = cleaned_data.get("leaver_email_address")

        if not for_self and not leaver_email_address:
            raise ValidationError(
                "If you are leaving the DIT, please check the 'I am "
                "leaving DIT' checkbox. If you are filling this form "
                "out for someone else, please provide their email "
                "address"
            )


class HardwareReceivedForm(GovFormattedModelForm):
    class Meta:
        model = LeavingRequest
        fields = (
            "hardware_received",
        )
