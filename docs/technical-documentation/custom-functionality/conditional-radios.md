# Radios with conditional content

In the GDS Design System, we have a pattern for [conditionally revealing a related question](https://design-system.service.gov.uk/components/radios/#conditionally-revealing-a-related-question). This is a pattern where a user is presented with further content that is contained within the radio selects.

To acheive this in this project we have added some simple JS that will find content that relates to a radio select and show/hide it based on the radio select being selected. (see: core/static/js/conditional-radios.js).

Since our forms are generated using Crispy Forms, you can use the [`radios_with_conditionals`](../../code-docs/leaver-forms/#leavers.forms.leaver.radios_with_conditionals) method to your form `__init__` method to apply the JS logic:

```python
from django import forms
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Layout, Size
from leavers.forms.leaver import radios_with_conditionals


class ExampleForm(forms.Form):
    how_many_fruit = forms.ChoiceField(
        label="How many fruit do you eat per day?",
        choices=(
            ("0", "None"),
            ("1", "One"),
            ("2", "Two"),
            ("3", "Three"),
            ("4", "Four"),
            ("5", "Five"),
            ("6", "Six"),
            ("7", "Seven"),
            ("8", "Eight"),
            ("9", "Nine"),
            ("10", "Ten"),
        )
        widget=forms.RadioSelect,
    )
    notes = forms.CharField(
        label="Notes",
        required=False,
        widget=forms.Textarea,
    )
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            radios_with_conditionals("how_many_fruit", legend_size=Size.MEDIUM),
        )

```

The [`radios_with_conditionals`](../../code-docs/leaver-forms/#leavers.forms.leaver.radios_with_conditionals) method is a wrapper to the `Field.radios` method, which means you can pass through the same arguments as you would to the `radios` method.

You can then add a wrapper `Div` with a `css_class` that dentotes which radio select it relates to:

```python
Div(
    Field.textarea("notes", rows=5)
    css_class="radio-conditional-field conditional-how_many_fruit-10",
),
```

It will need to contain the class `radio-conditional-field` and the class `conditional-{field_name}-{value}`. In the example above, the field name is `how_many_fruit` and the value is `10`, meaning that the content will be shown when the user selects the radio select with the value `10`.
