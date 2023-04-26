from django.contrib import admin

from core.beis_service_now.models import (
    ServiceNowAsset,
    ServiceNowDirectorate,
    ServiceNowUser,
)

admin.site.register(ServiceNowAsset)
admin.site.register(ServiceNowUser)
admin.site.register(ServiceNowDirectorate)
