from django.urls import path

from api.views import DetailCorrectionViewSet


urlpatterns = [
    path(
        "detail-correction/",
        DetailCorrectionViewSet.as_view({"get": "list"}),
        name="detail_correction",
    ),
]
