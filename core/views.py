from typing import Optional

from django.views.generic import TemplateView


class BaseTemplateView(TemplateView):
    """Inherit from this view when you want to use the core base.html template.

    The back_link_url attribute supports being set to a reverse_lazy url. It's difficult
    to type what reverse_lazy returns so it's being left out for now.

    Examples:
        Using reverse_lazy for the back_link_url:
        >>> from django.urls import reverse_lazy
        >>> class MyView(BaseTemplateView):
        ...     back_link_url = reverse_lazy("my-back-url")
    """

    back_link_url: Optional[str] = None
    back_link_text: Optional[str] = None

    def get_back_link_url(self):
        return self.back_link_url

    def get_back_link_text(self):
        return self.back_link_text

    def get_context_data(self, **kwargs):
        kwargs.update(
            back_link_url=self.get_back_link_url(),
            back_link_text=self.get_back_link_text(),
        )

        return super().get_context_data(**kwargs)
