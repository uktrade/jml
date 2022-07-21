from django import forms
from django.forms import RadioSelect


class WhoIsLeavingForm(forms.Form):
    CHOICES = [
        ("me", "Me"),
        ("someone_else", "Someone Else"),
    ]

    who_for = forms.ChoiceField(
        label="",
        choices=CHOICES,
        widget=RadioSelect,
    )
