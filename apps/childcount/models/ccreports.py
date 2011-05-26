#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga, rgaudin

from django.utils.translation import gettext as _

from django.db.models import F
from django.db.models import Avg, Count, Sum

import calendar
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from childcount.models import Patient
from locations.models import Location
from childcount.models import CHW, Clinic
from childcount.models import NutritionReport
from childcount.models import StillbirthMiscarriageReport
from childcount.models import MedicineGivenReport
from childcount.models import DangerSignsReport
from childcount.models import NeonatalReport
from childcount.models import FamilyPlanningReport
from childcount.models import FeverReport
from childcount.models import CodedItem
from childcount.models import ReferralReport
from childcount.models import BirthReport
from childcount.models import PregnancyReport, SPregnancy
from childcount.models import HouseholdVisitReport
from childcount.models import FollowUpReport
from childcount.models import ImmunizationSchedule
from childcount.models import ImmunizationNotification
from childcount.models import BedNetReport
from childcount.models import BednetIssuedReport
from childcount.models import BednetUtilization
from childcount.models import DrinkingWaterReport
from childcount.models import SanitationReport
from childcount.models import AppointmentReport
from childcount.models import UnderOneReport
from childcount.models import DeathReport

from childcount.utils import day_end, \
                                day_start, \
                                get_dates_of_the_week, \
                                get_median, \
                                seven_days_to_date, \
                                first_day_of_month, \
                                last_day_of_month, \
                                first_date_of_week

from logger.models import IncomingMessage, OutgoingMessage

class SummaryReport():

    '''Cluster-wide Summary Reports'''

    def num_of_patients(self):
        return Patient.objects.all().count()

    def num_of_underfive(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_pregnant(self):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        return {"summary": {"num_underfive": sr.num_of_underfive(), \
                            "num_patients": sr.num_of_patients(), \
                            "num_households": sr.num_of_households(), \
                            "num_pregnant": sr.num_pregnant()}}


class WeekSummaryReport():

    '''This week Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def savgummary(cls):
        sr = cls()
        endDate = datetime.today()
        startDate = endDate - timedelta(endDate.weekday())

        return {"week_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class MonthSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_MODERATE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"month_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}

class GeneralSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter().count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_MODERATE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE_COMP).count()


        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter().count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"general_summary_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


