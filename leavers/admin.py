from django.contrib import admin

from leavers.models import LeaverInformation, LeavingRequest, SlackMessage, TaskLog

admin.site.register(LeavingRequest)
admin.site.register(LeaverInformation)
admin.site.register(TaskLog)
admin.site.register(SlackMessage)
