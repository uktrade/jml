from rest_framework import serializers

from leavers.models import LeavingRequest


class LeavingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavingRequest
        fields = ["uuid"]
