#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin

from models import ReportMalaria

class ReportMalariaAdmin(admin.ModelAdmin):
    list_display = ("case","name","zone","result", "bednet","entered_at","provider","provider_number")
    verbose_name = "Malaria Report"
    verbose_name_plural = "Malaria Reports"

admin.site.register(ReportMalaria, ReportMalariaAdmin)
