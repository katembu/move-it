#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from reportgen.models import *

admin.site.register(Report)
admin.site.register(NightlyReport)
admin.site.register(GeneratedReport)

