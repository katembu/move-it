#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin

from models import Diagnosis, ReportDiagnosis

admin.site.register(Diagnosis)

class ReportDiagnosisAdmin(admin.ModelAdmin):
    list_display = ("case", "entered_at")

admin.site.register(ReportDiagnosis, ReportDiagnosisAdmin)
