from typing import TYPE_CHECKING, Dict

from dit_activity_stream.client import ActivityStreamClient
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class ActivityStreamUserClient(ActivityStreamClient):
    object_uuid_field: str = "user_id"
    object_last_modified_field: str = "last_modified"

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return User.objects.all()

    def render_object(self, object: "User") -> Dict:
        return {
            "id": object.id,
            "username": object.username,
            "first_name": object.first_name,
            "last_name": object.last_name,
        }
