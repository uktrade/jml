from django import template

register = template.Library()


@register.simple_tag
def search_result_additional_information(*args) -> str:
    parts = [str(part) for part in args if part]

    if not parts:
        return ""

    return f"({', '.join(parts)})"
