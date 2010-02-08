#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin

from childcount.models import Configuration
from childcount.models import Case
from childcount.models import Patient
from childcount.models import Referral

admin.site.register(Configuration)
admin.site.register(Case)
admin.site.register(Patient)
admin.site.register(Referral)
