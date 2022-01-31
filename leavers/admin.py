from django.contrib import admin

from leavers.models import LeavingRequest, SlackMessage, TaskLog

admin.site.register(LeavingRequest)
admin.site.register(TaskLog)
admin.site.register(SlackMessage)
