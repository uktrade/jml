from django import template

from core.utils.helpers import make_possessive

register = template.Library()


@register.filter
def possessive(value):
    return make_possessive(value)


@register.simple_tag(takes_context=True)
def get_current_url_with_query_params(context, **kwargs):
    request = context["request"]
    query_params = request.GET.copy()
    for key, value in kwargs.items():
        query_params[key] = value
    return request.path + "?" + query_params.urlencode()
