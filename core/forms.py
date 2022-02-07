from django import forms
from django.forms.widgets import (
    CheckboxInput,
    EmailInput,
    RadioSelect,
    Select,
    Textarea,
    TextInput,
)


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
            if isinstance(widget, RadioSelect):
                widget.attrs.update({"class": "govuk-radios__input"})
            elif isinstance(widget, Select):
                widget.attrs.update({"class": "govuk-select"})
            elif isinstance(widget, CheckboxInput):
                widget.attrs.update({"class": "govuk-checkboxes__input"})
            elif isinstance(widget, TextInput) or isinstance(widget, EmailInput):
                widget.attrs.update({"class": "govuk-input"})


class YesNoField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = (
            ("yes", "Yes"),
            ("no", "No"),
        )
        kwargs["widget"] = RadioSelect
        super().__init__(*args, **kwargs)
