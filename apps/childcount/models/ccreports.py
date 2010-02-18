#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext_lazy as _

from childcount.models import Patient
from childcount.models.reports import MUACReport


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
