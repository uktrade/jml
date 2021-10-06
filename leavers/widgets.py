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
    #
    # def subwidgets(self, name, value, attrs=None):
    #     if self.is_localized:
    #         for widget in self.widgets:
    #             widget.is_localized = self.is_localized
    #     # value is a list of values, each corresponding to a widget
    #     # in self.widgets.
    #     if not isinstance(value, list):
    #         value = self.decompress(value)
    #     output = []
    #     final_attrs = self.build_attrs(attrs)
    #     id_ = final_attrs.get('id')
    #     for i, widget in enumerate(self.widgets):
    #         try:
    #             widget_value = value[i]
    #         except IndexError:
    #             widget_value = None
    #         if id_:
    #             final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
    #         output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))
    #
    #     return output
