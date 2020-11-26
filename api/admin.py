from django.contrib import admin

from .models import (
    Org, OrgUser, Ping, PingHeader,
    Result, Failure, PongData, Schedule
)

admin.site.register(Org)
admin.site.register(OrgUser)
admin.site.register(Ping)
admin.site.register(PingHeader)
admin.site.register(Result)
admin.site.register(Failure)
admin.site.register(PongData)
admin.site.register(Schedule)
