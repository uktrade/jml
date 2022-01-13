from django import forms

from core.forms import GovFormattedForm


class SearchForm(GovFormattedForm):
    search_terms = forms.CharField(
        label="Find the member of staff using their name or email"
    )
