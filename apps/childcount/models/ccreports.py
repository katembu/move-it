#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext as _

from datetime import date, timedelta

from childcount.models import Patient
from childcount.models import CHW
from childcount.models.reports import NutritionReport 
from childcount.models.reports import HouseHoldVisitReport

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

    @classmethod
    def patients_summary_list(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name, \
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name, \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name"), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name, \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _('age'), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _('Last muac'), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name, \
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
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        num = Patient.objects.filter(chw=self, dob__lte=sixtym).count()
        return num

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
        num = HouseHoldVisitReport.objects.filter(created_by=self).count()
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

    @classmethod
    def muac_summary(cls):
        num_healthy = NutritionReport.objects.filter(status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = NutritionReport.objects.filter(status=NutritionReport.STATUS_MODERATE).count()
        num_sam = NutritionReport.objects.filter(status=NutritionReport.STATUS_SEVERE).count()
        num_comp = NutritionReport.objects.filter(status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()
        info = {'%s%% HEALTHY' % round((num_healthy / float(num_eligible)) * 100): num_healthy,
                '%s%% MAM' % round((num_mam / float(num_eligible)) * 100): num_mam,
                '%s%% SAM' % round((num_sam / float(num_eligible)) * 100): num_sam,
                '%s%% SAM+' % round((num_comp / float(num_eligible)) * 100): num_comp}
        return info 

    @classmethod
    def total_at_risk(cls):
        num = NutritionReport.objects.filter(status__in=(NutritionReport.STATUS_SEVERE, \
                                            NutritionReport.STATUS_SEVERE_COMP, \
                                            NutritionReport.STATUS_MODERATE)).count()
        return num

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('alias').verbose_name, \
             'bit': '@{{ object.alias }}'})
        columns.append(
            {'name': _("Name"), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name, \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': "No. of Patients", \
             'bit': '{{ object.num_of_patients }}'})
        columns.append(
            {'name': "No. Under 5", \
             'bit': '{{ object.num_of_underfive }}'})
        columns.append(
            {'name': "No. of Visits", \
             'bit': '{{ object.num_of_visits }}'})
        columns.append(
            {'name': "No. SAM", \
             'bit': '{{ object.num_of_sam }}'})
        columns.append(
            {'name': "No. MAM", \
             'bit': '{{ object.num_of_mam }}'})
        columns.append(
            {'name': "No. HEALTHY", \
             'bit': '{{ object.num_of_healthy }}'})
        columns.append(
            {'name': "No. SMS Sent", \
             'bit': '{{ object.num_of_sms }}'})

        sub_columns = None
        return columns, sub_columns
