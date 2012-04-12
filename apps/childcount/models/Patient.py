#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import date, timedelta

from django import db
from django.db import models
from django.db import connection
from django.db.models import F
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _
from django.forms import CharField
import reversion

from reporters.models import Reporter
from locations.models import Location

from indicator.cache import cache_simple

import childcount.models.CHW


class Patient(models.Model):
    """Holds the details of Birth and Death, 
    properties and methods related to it
    """

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_patient'
        verbose_name = _(u"Registration")
        verbose_name_plural = _(u"Registrations")
        #ordering = ('health_id', )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))
    """Patient genders"""

    STATUS_FAILED = 0
    STATUS_SUCCESSFULL = 1
    STATUS_NOTSTARTED = 2

    OXD_STATUS_CHOICES = (
        (STATUS_FAILED, _(u"Failed")),
        (STATUS_SUCCESSFULL, _(u"Successfull")),
        (STATUS_NOTSTARTED, _(u"Not Started")))
    '''Status options for OpenXdata SYNCHRONIZATION '''

    DEATH = 0
    BIRTH = 1

    EVENT_TYPE_CHOICES = (
        (DEATH, _(u"Death")),
        (BIRTH, _(u"Birth")))

    HEALTH_FACILITY = 'C'
    HOME_FACILITY = 'H'

    PLACE_CHOICES = (
				(HEALTH_FACILITY, _(u"Hospital Clinic")),
				(HOME_FACILITY, _(u"Home")))
    '''Death place options '''

    CERT_COLLECTED = 'C'
    CERT_READY = 'R'
    CERT_VERIFIED = 'N'
    CERT_UNVERIFIED = 'U'    
    CERT_INVALID = 'I'


    CERT_CHOICES = (
                (CERT_COLLECTED, _(u"Certificate Collected")),
                (CERT_READY, _(u"Certificate Ready. Not collected")),
                (CERT_VERIFIED, _(u"Details collected. Valid")),
                (CERT_INVALID, _(u"Invalid")),
                (CERT_UNVERIFIED, _(u"Not verified ")))

    health_id = models.CharField(_(u"Event ID"), max_length=6, blank=True, \
                                null=True, db_index=True, unique=True, \
                                help_text=_(u"Unique Event ID"))
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)

    first_name = models.CharField(_(u"First name"), max_length=100)
    last_name = models.CharField(_(u"Last name"), max_length=50, \
                                 help_text=_(u"Family name or surname"))
    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    event_type = models.CharField(_(u"Event Type"), max_length=1, \
                              choices=EVENT_TYPE_CHOICES)
    notification_no = models.CharField(_(u"Notification no"), max_length=12, \
                              blank=True, default='U', null=True)
    place = models.CharField(_(u"Birth / Death Place"), max_length=1, \
                              choices=PLACE_CHOICES )
    cert_status = models.CharField(_(u"Certificate Status"), max_length=1, \
                                     choices = CERT_CHOICES, \
                                     default = CERT_UNVERIFIED)
    dob = models.DateField(_(u"Date of Birth"), null=True, blank=True)
    dod = models.DateField(_(u"Date of Death"), null=True, blank=True)
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation.")) 
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Community Health Worker"))
    location = models.ForeignKey(Location, blank=True, null=True, \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The location this person " \
                                              "lives within"))
    mobile = models.CharField(_(u"Mobile phone number"), max_length=16, \
                              blank=True, null=True)
    sync_oxd = models.CharField(_(u"OpenXdata Sync"), max_length=1, \
                                     choices = OXD_STATUS_CHOICES, \
                                     default = STATUS_NOTSTARTED)

    def get_dictionary(self):
        days, months = self.age_in_days_months()
        return {'full_name': '%s %s' % (self.first_name, self.last_name),
                'age': '%sm' % months,
                'days': days,
                'mobile': self.mobile,
                'status': self.STATUS_CHOICES.index(self.status),
                'chw': self.chw,
                'gender': self.gender}

    def age_in_days_weeks_months(self, relative_to=date.today()):
        """return the age of the patient in days and in months
        
        :param relative_to: Date from which to compute the patient's age
        :type relative_to: :class:`datetime.date`
        """
        days = (relative_to - self.dob).days
        weeks = days / 7
        months = int(days / 30.4375)
        return days, weeks, months

    def years(self):
        """Calculate patient's age in years"""
        days, weeks, months = self.age_in_days_weeks_months()
        return months / 12

    def humanised_age(self):
        """return a string containing a human readable age"""
        days, weeks, months = self.age_in_days_weeks_months()
        if weeks < 2:
            return _(u"%(weeks)sweek") % {'weeks': weeks}
        if weeks < 12:
            return _(u"%(weeks)sweeks") % {'weeks': weeks}
        elif months < 60:
            return _(u"%(months)smonths") % {'months': months}
        else:
            years = months / 12
            return _(u"%(years)syears") % {'years': years}

    def full_name(self):
        """Return the patients first and last names"""
        return ' '.join([self.first_name, self.last_name])

    def __unicode__(self):
        return u'%s' % (self.full_name())

    @classmethod
    def is_valid_health_id(cls, health_id):
        """Naive check if a health ID is valid

        :param health_id: Health ID to check
        :type health_id: str

        :returns: bool
        """

        MIN_LENGTH = 4
        MAX_LENGTH = 4
        BASE_CHARACTERS = '0123456789acdefghjklmnprtuvwxy'

        try:
            health_id = unicode(health_id)
            health_id = health_id.lower()
        except:
            return False

        if len(health_id) < MIN_LENGTH or len(health_id) > MAX_LENGTH:
            return False

        for char in health_id:
            if char not in BASE_CHARACTERS:
                return False

        # TODO checkbit

        return True

    @classmethod
    def registrations_by_date(cls):
        """Number of patients registered per day

        :returns: Iterable of (`datetime.date`, n_registrations) tuples
        """

        conn = connection.cursor()
        by_date = conn.execute(
            'SELECT DATE(`created_on`), COUNT(*) FROM `cc_patient` \
                GROUP BY DATE(`created_on`) ORDER BY DATE(`created_on`) ASC;')

        # Data comes back in an iterable of (date, count) tuples
        raw_data = conn.fetchall()
        dates = []
        counts = []
        agg = 0
        for pair in raw_data:
            dates.append((pair[0] - date.today()).days)
            agg += pair[1]
            counts.append(agg)
        return (dates, counts)

    @classmethod
    def table_columns(cls):
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
            {'name': _(u"Age"), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name, \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns

reversion.register(Patient)
