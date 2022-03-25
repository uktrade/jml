from datetime import date

from django import forms


class DateSelectorWidget(forms.MultiWidget):
    """
    TODO: Replace all usage of this widget with crispy_forms_gds.fields.DateInputField
    """

    input_type = "date_multi_field"
    hint = ""

    @property
    def day(self):
        return self.widgets[0]

    @property
    def month(self):
        return self.widgets[1]

    @property
    def year(self):
        return self.widgets[2]

    def __init__(self, hint="", attrs=None):
        self.hint = hint
        widgets = [
            forms.NumberInput(),
            forms.NumberInput(),
            forms.NumberInput(),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str):
            year, month, day = value.split("-")
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        day, month, year = super().value_from_datadict(data, files, name)
        if day or month or year:
            return "{}-{}-{}".format(year, month, day)

        return None
