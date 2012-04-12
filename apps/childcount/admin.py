#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.contrib import admin
from reversion.admin import VersionAdmin
from reversion.models import Version, Revision

from childcount.models import *


admin.site.register(Configuration)
admin.site.register(CHW)

class PatientAdmin(VersionAdmin):
    list_display = ('health_id', '__unicode__', 'location', 'chw', 'cert_status')
    search_fields = ['first_name', 'last_name']
    list_filter = ['cert_status', 'event_type', 'dob', 'chw']
admin.site.register(Patient, PatientAdmin)


admin.site.register(Version)
admin.site.register(Revision)
