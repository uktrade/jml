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
