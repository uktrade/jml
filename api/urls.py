from api.views import DetailCorrectionViewSet
from django.urls import path

urlpatterns = [
    path(
        "detail-correction/",
        DetailCorrectionViewSet.as_view({"get": "list"}),
        name="detail_correction",
    ),
]
