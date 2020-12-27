from django.contrib import admin

from .models import (
    Org, OrgUser, Ping, PingHeader,
    Result, Failure, Schedule, Metric, VitalInstance
)

admin.site.register(Org)
admin.site.register(OrgUser)
admin.site.register(Ping)
admin.site.register(PingHeader)
admin.site.register(Result)
admin.site.register(Failure)
admin.site.register(Schedule)
admin.site.register(Metric)
admin.site.register(VitalInstance)
