from typing import Dict

from django import forms
from django.forms.widgets import RadioSelect


class YesNoField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = (
            ("yes", "Yes"),
            ("no", "No"),
        )
        kwargs["widget"] = RadioSelect
        super().__init__(*args, **kwargs)


class BaseForm(forms.Form):
    required_error_messages: Dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, required_message in self.required_error_messages.items():
            self.fields[field_name].error_messages["required"] = required_message
