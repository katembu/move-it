#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext_lazy as _

from datetime import date, timedelta

from childcount.models import Patient
from childcount.models import CHW
from childcount.models.reports import MUACReport
from childcount.models.reports import HouseHoldVisitReport


class ThePatient(Patient):

    class Meta:
        proxy = True

    def latest_muac(self):
        muac = MUACReport.objects.filter(patient=self).latest()
        if not None:
            return u"%smm %s" % (muac.muac, muac.verbose_state)
        return u""

    @classmethod
    def patients_summary_list(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name, \
            'bit': '{{object.household.health_id}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name, \
            'bit': '{{object.health_id}}'})
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
    def num_of_visits(self):
        '''The number of visits in the last 7 days'''
        seven = date.today() - timedelta(7)
        num = HouseHoldVisitReport.objects.filter(created_by=self).count()
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
            {'name': "No, of Patients Under 5", \
             'bit': '{{ object.num_of_underfive }}'})
        columns.append(
            {'name': "No. of Visits", \
             'bit': '{{ object.num_of_visits }}'})

        sub_columns = None
        return columns, sub_columns
