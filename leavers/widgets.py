from datetime import date
from django import forms


class DateSelectorWidget(forms.MultiWidget):
    input_type = "date_multi_field"

    @property
    def test(self):
        return "test"

    @property
    def day(self):
        return self.widgets[0]

    def __init__(self, attrs=None):
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
            year, month, day = value.split('-')
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        day, month, year = super().value_from_datadict(data, files, name)
        return '{}-{}-{}'.format(year, month, day)
