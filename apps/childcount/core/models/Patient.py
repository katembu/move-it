#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Patient - Patient model
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import datetime

from reporters.models import Reporter
from locations.models import Location

from childcount.core.models.fields import GenderField
from childcount.core.models.locations import Clinic, Zone

from childcount.core.models.CHW import CHW


class Patient(GenderField):

    '''Holds the patient details, properties and methods related to it'''

    class Meta:
        app_label = 'childcount'

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    STATUS_DEAD = -1

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Alive')),
        (STATUS_INACTIVE, _('Relocated')),
        (STATUS_DEAD, _('Dead')))

    health_id = models.CharField(_(u"Health ID"), max_length=6, blank=True, \
                                null=True, db_index=True, unique=True, \
                                help_text=_(u"Unique six character Health ID"))
    first_name = models.CharField(_(u"First name"), max_length=32)
    middle_name =  models.CharField(_(u"Middle name"), max_length=32, \
                                   blank=True, null=True)
    last_name = models.CharField(_(u"Last name"), max_length=32, \
                                 help_text=_(u"Family name or surname"))
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation"))
    guardian = models.ForeignKey('self', blank=True, null=True, \
                                 verbose_name=_(u"Mother or guardian"), \
                                 related_name='child')
    household = models.ForeignKey('self', \
                                  verbose_name=_(u"Household's primary " \
                                                 "caregiver"), \
                                  help_text=_(u"The primary caregiver in " \
                                              "this person's household " \
                                              "(self if primary caregiver)"), \
                                  related_name='household_member')
    chw = models.ForeignKey(CHW, db_index=True,
                            verbose_name=_(u"Community health worker"))
    zone = models.ForeignKey(Zone, blank=True, null=True,
                             verbose_name=_(u"Location"), \
                             help_text=_(u"The location this person lives " \
                                          "within"))
    clinic = models.ForeignKey(Clinic, blank=True, null=True, \
                               verbose_name=_(u"Health facility"), \
                               help_text=_(u"The primary health facility " \
                                            "that this patient visits"))
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)
    mobile = models.CharField(_(u"Mobile phone number"), max_length=16, \
                              blank=True, null=True)
    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)

    def get_dictionary(self):
        days, months = self.age_in_days_months()
        return {'full_name': '%s %s' % (self.first_name, self.last_name),
                'age': '%sm' % months,
                'days': days,
                'clinic': self.clinic,
                'mobile': self.mobile,
                'status': self.STATUS_CHOICES.index(self.status),
                'chw': self.chw,
                'gender': self.gender,
                'guardian': self.guardian}

    def age_in_days_months(self):
        '''return the age of the patient in days and in months'''
        days = (datetime.now() - self.dob).days
        months = int(days / 30.4375)
        return days, months
