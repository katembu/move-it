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

from childcount.core.models.CHW import CHW


class Patient(models.Model):

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

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')))

    health_id = models.CharField(_('Patient ID #'), null=True, \
                                  db_index=True, max_length=10,
                                  unique=True)
    first_name = models.CharField(max_length=255, db_index=True)
    middle_name =  models.CharField(max_length=255, db_index=True, \
                                    null=True, blank=True)
    last_name = models.CharField(max_length=255, db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, \
                              null=True, blank=True)
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    estimated_dob = models.NullBooleanField(null=True, blank=True)
    guardian = models.ForeignKey(Reporter, db_index=True)
    household = models.ForeignKey(Reporter, db_index=True)
    chw = models.ForeignKey(CHW, db_index=True)
    zone = models.ForeignKey(Location, db_index=True)
    clinic = models.ForeignKey(Location, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    mobile =  models.CharField(max_length=255, db_index=True, \
                                    null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)
