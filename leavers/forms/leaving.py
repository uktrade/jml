from django import forms

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
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
    )

    last_day = forms.DateField(
        label="",
        widget=DateSelectorWidget(hint="For example, 27 3 2007"),
        required=False,
    )
