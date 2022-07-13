from django.urls import path

from core.landing_pages import views

urlpatterns = [
    path(
        "beta/leavers-and-line-managers/",
        views.leaver_landing_page,
        name="leaver-landing-page",
    ),
    path(
        "beta/data-processors/",
        views.data_processor_landing_page,
        name="data-processors-landing-page",
    ),
]
