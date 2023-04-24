from django import template
from django.template.defaulttags import URLNode, url

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


@register.simple_tag(takes_context=True)
def get_current_url_without_query_params(context, **kwargs):
    request = context["request"]
    return request.path


class URLNodeWithUrlQuery(URLNode):
    def render(self, context) -> str:
        request = context["request"]
        query_params = request.GET.copy()
        return super().render(context) + "?" + query_params.urlencode()

    @classmethod
    def from_url_node(cls, url_node: URLNode):
        return cls(
            view_name=url_node.view_name,
            args=url_node.args,
            kwargs=url_node.kwargs,
            asvar=url_node.asvar,
        )


@register.tag
def url_with_query_params(parser, token):
    url_node = url(parser, token)
    custom_url_node = URLNodeWithUrlQuery.from_url_node(url_node)
    return custom_url_node
