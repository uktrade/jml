from dataclasses import dataclass

from django.utils.safestring import mark_safe
from govuk_frontend_django.components.base import GovUKComponent


@dataclass(kw_only=True)
class GovUKLink(GovUKComponent):
    href: str
    text: str

    def render(
        self,
        template_name=None,
        context=None,
        renderer=None,
        component_data=None,
    ):
        data = self.__dict__.copy()
        href = data["href"]
        text = data["text"]
        return mark_safe(f"<a class='govuk-link' href='{href}'>{text}</a>")

    __str__ = render
    __html__ = render
