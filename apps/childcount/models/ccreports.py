#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext as _
from django.db.models import F

from datetime import date, timedelta

from childcount.models import Patient
from childcount.models import CHW
from childcount.models import NutritionReport, FeverReport,ReferralReport
from childcount.models import BirthReport
from childcount.models import HouseholdVisitReport

from childcount.utils import day_end, day_start, get_dates_of_the_week

from logger.models import IncomingMessage


class ThePatient(Patient):

    class Meta:
        verbose_name = _("Patient List Report")
        proxy = True

    def latest_muac(self):
        muac = NutritionReport.objects.filter(patient=self).latest()
        if not None:
            return u"%smm %s" % (muac.muac, muac.verbose_state)
        return u""

    def check_visit_within_seven_days_of_birth(self):
        seven_days_after_birth = self.dob + timedelta(7)
        hvr = HouseholdVisitReport.objects\
                .filter(encounter__encounter_date__gt=self.dob, \
                    encounter__encounter_date__lte=seven_days_after_birth)\
                .count()
        if hvr:
            return True
        else:
            return False

    def visit_within_90_days_of_last_visit(self):
        try:
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household).latest()
            latest_date = hvr.encounter.encounter_date
            old_date = ldate - timedelta(90)
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household, \
                                encunter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if hvr.count():
                return True
            return False
        except HouseholdVisitReport.DoesNotExist:
            return False

    def ontime_muac(self):
        try:
            nr = NutritionReport.objects.filter(encounter_patient=self).latest()
            latest_date = nr.encounter.encounter_date
            old_date = ldate - timedelta(90)
            nr = NutritionReport.objects.filter(encounter_patient=self, \
                                encunter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if nr.count():
                return True
            return False
        except NutritionReport.DoesNotExist:
            return False

    @classmethod
    def under_five(cls, chw=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        if chw:
            p = cls.objects.filter(dob__gte=sixtym, \
                                       chw=chw).order_by("household")
        else:
            p = cls.objects.filter(dob__gte=sixtym).order_by("household")
        return p

    @classmethod
    def patients_summary_list(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name.upper(), \
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name.upper(), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name".upper()), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _("Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _("Last muac".upper()), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name.upper(), \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns


class TheCHWReport(CHW):

    class Meta:
        verbose_name = _("Community Health Worker Report")
        proxy = True

    @property
    def num_of_patients(self):
        num = Patient.objects.filter(chw=self).count()
        return num

    @property
    def num_of_underfive(self):
        return self.patient_under_five().count()

    def patients_under_five(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(chw=self, dob__lte=sixtym)

    @property
    def num_of_sam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            status=NutritionReport.STATUS_SEVERE_COMP).count()
        num += NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_SEVERE).count()
        return num

    @property
    def num_of_mam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_MODERATE).count()
        return num

    @property
    def num_of_healthy(self):
        num = NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_HEALTHY).count()
        return num

    @property
    def num_of_visits(self):
        '''The number of visits in the last 7 days'''
        seven = date.today() - timedelta(7)
        num = HouseholdVisitReport.objects.filter(created_by=self).count()
        return num

    @property
    def num_muac_eligible(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(chw=self, dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @classmethod
    def total_muac_eligible(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @property
    def num_of_sms(self):
        identity = self.connection().identity
        num = IncomingMessage.objects.filter(identity=identity).count()
        return num

    def number_of_households(self):
        return self.households().count()

    def households(self):
        return Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self)

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_visits(self):
        households = self.households()
        num_on_time = 0
        for household in households:
            if household.visit_within_90_days_of_last_visit():
                num_on_time += 1
        if num_on_time is 0:
            return 0
        else:
            total_households = households.count()
            return round((num_on_time/float(total_households))*100)

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                        clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).coun()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return 0
        return (round(num_of_clinic_delivery/float(num_of_births))*100)

    def num_underfive_refferred(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        rr = ReferralReport.objects.filter(encounter__patient__dob__lte=sixtym)
        return rr.count()

    def num_underfive_malaria(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        fr = FeverReport.objects.filter(encounter__patient__dob__lte=sixtym)
        return fr.count()
    
    def num_underfive_diarrhea(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        fr = FeverReport.objects.filter(encounter__patient__dob__lte=sixtym)
        return fr.count()

    def percentage_ontime_muac(self):
        underfives = self.patients_under_five()
        count = 0
        for achild in underfives:
            if achild.ontime_muac():
                count += 1
        if not count:
            return count
        else:
            total_count = underfives.count()
            return round(100 * (count/float(total_count)))

    def num_of_active_sam_cases(self):
        count = 0
        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        nr = NutritionReport.objects\
                        .filter(chw=self, status__in=danger)\
                        .values('encounter__patient').distinct()
        for r in nr:
            p = Patient.objects.get(id=r['encounter_patient'])
            latest = Nutrition.objects.filter(encounter_patient=p).latest()
            if latest.status in danger:
                count += 1
        return count

    @classmethod
    def muac_summary(cls):
        num_healthy = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()
        info = {'%s%% HEALTHY' %\
                round((num_healthy / float(num_eligible)) * 100): num_healthy,
                '%s%% MAM' %\
                    round((num_mam / float(num_eligible)) * 100): num_mam,
                '%s%% SAM' %\
                    round((num_sam / float(num_eligible)) * 100): num_sam,
                '%s%% SAM+' %\
                    round((num_comp / float(num_eligible)) * 100): num_comp}
        return info

    @classmethod
    def total_at_risk(cls):
        num = NutritionReport.objects.filter(\
                                status__in=(NutritionReport.STATUS_SEVERE, \
                                NutritionReport.STATUS_SEVERE_COMP, \
                                NutritionReport.STATUS_MODERATE)).count()
        return num

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('alias').verbose_name.upper(), \
             'bit': '@{{ object.alias }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': "No. of Patients".upper(), \
             'bit': '{{ object.num_of_patients }}'})
        columns.append(
            {'name': "No. Under 5".upper(), \
             'bit': '{{ object.num_of_underfive }}'})
        columns.append(
            {'name': "No. of Visits".upper(), \
             'bit': '{{ object.num_of_visits }}'})
        columns.append(
            {'name': "No. SAM".upper(), \
             'bit': '{{ object.num_of_sam }}'})
        columns.append(
            {'name': "No. MAM".upper(), \
             'bit': '{{ object.num_of_mam }}'})
        columns.append(
            {'name': "No. HEALTHY".upper(), \
             'bit': '{{ object.num_of_healthy }}'})
        columns.append(
            {'name': "No. SMS Sent".upper(), \
             'bit': '{{ object.num_of_sms }}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def sms_per_day(cls):
        days_of_the_week = get_dates_of_the_week()
        data = {}
        for day in days_of_the_week:
            start = day_start(day['date'])
            end = day_end(day['date'])
            num = IncomingMessage.objects.filter(received__gte=start, \
                                           received__lte=end).count()
            data.update({day["day"]: num})
        return data
