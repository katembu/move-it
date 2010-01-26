#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin

from childcount.core.models.Config import Configuration
from childcount.core.models.Case import Case, CaseNote
from childcount.core.models.Observation import Observation
from childcount.core.models.Patient import Patient
from childcount.core.models.Referral import Referral

admin.site.register(Configuration)
admin.site.register(Case)
admin.site.register(CaseNote)
admin.site.register(Observation)
admin.site.register(Patient)
admin.site.register(Referral)
