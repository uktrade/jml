from django.contrib import admin

from leavers.models import LeavingRequest, SlackMessage, TaskLog  # /PS-IGNORE

admin.site.register(LeavingRequest)
admin.site.register(TaskLog)
admin.site.register(SlackMessage)
