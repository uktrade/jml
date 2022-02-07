from django import forms
from django.forms import RadioSelect

from core.forms import GovFormattedForm
from leavers.widgets import DateSelectorWidget


class WhoIsLeavingForm(GovFormattedForm):
    CHOICES = [
        ("me", "Me"),
        ("someone_else", "Someone Else"),
    ]

    who_for = forms.ChoiceField(
        label="",
        choices=CHOICES,
        widget=RadioSelect,
    )

    last_day = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=False,
    )
