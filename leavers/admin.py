from django.contrib import admin

from leavers.models import LeavingRequest, TaskLog, SlackMessage

admin.site.register(LeavingRequest)
admin.site.register(TaskLog)
admin.site.register(SlackMessage)
