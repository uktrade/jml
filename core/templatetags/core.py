from django import template

from core.utils.helpers import make_possessive

register = template.Library()


@register.filter
def possessive(value):
    return make_possessive(value)
