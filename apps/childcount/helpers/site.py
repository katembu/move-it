#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import datetime

from django.utils.translation import gettext as _

from childcount.models import Patient

from childcount.indicators import nutrition
from childcount.indicators import fever
from childcount.indicators import registration
from childcount.indicators import pregnancy

def summary_stats(period):
    patients = Patient.objects.all()
    return {
        'num_mam_sam': nutrition.SamOrMam(period, patients),
        'num_rdt': fever.RdtPositive(period, patients),
        'num_underfive': registration.UnderFive(period, patients), 
        'num_patients': registration.Total(period, patients),
        'num_households': registration.Household(period, patients),
        'num_pregnant': pregnancy.Total(period, patients),
    }


