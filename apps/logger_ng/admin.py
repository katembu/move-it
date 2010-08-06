#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from logger_ng.models import LoggedMessage


class LoggedMessageAdmin(admin.ModelAdmin):
    list_filter = ['direction']
    search_fields = ['reporter__first_name', 'reporter__last_name', 'text']
    date_hierarchy = 'date'
admin.site.register(LoggedMessage, LoggedMessageAdmin)
