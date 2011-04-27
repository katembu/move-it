#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Patient - Patient model
'''

from datetime import date, timedelta

from django.db import models
from django.db.models import F
from django.db import connection
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _
from django.forms import CharField
import reversion

from reporters.models import Reporter
from locations.models import Location

import childcount.models.Clinic
import childcount.models.CHW

def queries():
    print len(connection.queries)
    connection.queries = []

class PatientManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)

class Patient(models.Model):

    '''Holds the patient details, properties and methods related to it'''
    class Meta:
        app_label = 'childcount'
        db_table = 'cc_patient'
        verbose_name = _(u"Patient")
        verbose_name_plural = _(u"Patients")
        ordering = ('health_id', )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    STATUS_DEAD = -1

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _(u"Alive")),
        (STATUS_INACTIVE, _(u"Relocated")),
        (STATUS_DEAD, _(u"Dead")))

    objects = PatientManager()
    health_id = models.CharField(_(u"Health ID"), max_length=6, blank=True, \
                                null=True, db_index=True, unique=True, \
                                help_text=_(u"Unique Health ID"))
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)

    first_name = models.CharField(_(u"First name"), max_length=100)
    last_name = models.CharField(_(u"Last name"), max_length=50, \
                                 help_text=_(u"Family name or surname"))
    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    dob = models.DateField(_(u"Date of Birth"), null=True, blank=True)
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation."))
    mother = models.ForeignKey('self', blank=True, null=True, \
                               verbose_name=_(u"Mother or Guardian."), \
                               related_name='child')
    household = models.ForeignKey('self', blank=True, null=True, \
                                  verbose_name=_(u"Head of House"), \
                                  help_text=_(u"The primary caregiver in " \
                                               "this person's household " \
                                               "(self if primary caregiver)"),\
                                  related_name='household_member')
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Community Health Worker"))
    location = models.ForeignKey(Location, blank=True, null=True, \
                                 related_name='resident', \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The location this person " \
                                              "lives within"))
    clinic = models.ForeignKey('Clinic', blank=True, null=True, \
                               verbose_name=_(u"Health facility"), \
                               help_text=_(u"The primary health facility " \
                                            "that this patient visits"))

    mobile = models.CharField(_(u"Mobile phone number"), max_length=16, \
                              blank=True, null=True)
    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)
    hiv_status = models.NullBooleanField(_(u"HIV Status"),
                                            blank=True, null=True)
    hiv_exposed = models.NullBooleanField(_(u"HIV Exposed?"),
                                            blank=True, null=True)

    def is_head_of_household(self):
        return self.household == self

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

    def age_in_days_weeks_months(self, relative_to=date.today()):
        '''return the age of the patient in days and in months'''
        days = (relative_to - self.dob).days
        weeks = days / 7
        months = int(days / 30.4375)
        return days, weeks, months

    def years(self):
        days, weeks, months = self.age_in_days_weeks_months()
        return months / 12

    def humanised_age(self):
        '''return a string containing a human readable age'''
        days, weeks, months = self.age_in_days_weeks_months()
        if days < 21:
            return _(u"%(days)sd") % {'days': days}
        elif weeks < 12:
            return _(u"%(weeks)sw") % {'weeks': weeks}
        elif months < 60:
            return _(u"%(months)sm") % {'months': months}
        else:
            years = months / 12
            return _(u"%(years)sy") % {'years': years}

    def full_name(self):
        return ' '.join([self.first_name, self.last_name])

    def __unicode__(self):
        return u'%s %s %s/%s' % (self.health_id.upper(), self.full_name(), \
                                 self.gender, self.humanised_age())

    @classmethod
    def is_valid_health_id(cls, health_id):
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

    #
    # BEGIN Indicator Code
    #

    ''' This enables us to extend patient QuerySets with
        useful filters
    '''
    objects = PatientManager()
    class QuerySet(QuerySet):
        def alive(self, start, end):
            return self\
                .exclude(status=Patient.STATUS_INACTIVE)\
                .exclude(encounter__ccreport__deathreport__death_date__lte=end)
        '''
        Age-related filters
        '''
        def neonatal(self, start, end):
            return self.age(start, end, 0, 28)
        
        def under_six_months(self, start, end):
            return self.age(start, end, 0, 30*6)

        def muac_eligible(self, start, end):
            return self.age(start, end, 6*30, 5*365)

        def under_one(self, start, end):
            return self.age(start, end, 0, 365)

        def under_five(self, start, end):
            return self.age(start, end, 0, 5*365)

        def under_nine(self, start, end):
            return self.age(start, end, 0, 9*365)

        def over_five(self, start, end):
            return self.age(start, end, 5*365, None)

        def age(self, start, end, min_days, max_days):
            filter_on = {}
            if min_days:
                filter_on['dob__lte'] = end-timedelta(days=min_days)
            if max_days:
                filter_on['dob__gt'] = end-timedelta(days=max_days)

            # We filter on dob__lte=end because we never want to 
            # include people who were not born at date end
            return self\
                .alive(start, end)\
                .filter(**filter_on)\
                .filter(dob__lte=end)

        '''
        Household filter
        '''
        def households(self, start, end):
            return self\
                .alive(start, end)\
                .filter(pk=F('household__pk'))


        '''
        Pregnancy filters
        '''
        def pregnant(self, start, end):
            return self.pregnant_months(start, end, 1, 9)

        def pregnant_months(self, start, end, start_month, end_month):
            assert start_month > 0, _("Start month must be > 0")
            assert start_month <= end_month, \
                        _("Start month must be <= end_month")

            # Filter out dead people, men, kids, and people 
            # less than 10 yrs or more than 55 yrs old...
            # Then look for women with PregnancyReports
            fil = self\
                .alive(start, end)\
                .filter(gender=Patient.GENDER_FEMALE)\
                .age(start, end, 10*365, 55*365)\
                .filter(encounter__ccreport__pregnancyreport__encounter__encounter_date__gte=\
                                        start-timedelta(days=365),
                        encounter__ccreport__pregnancyreport__encounter__encounter_date__lte=\
                    end)

            pks = set()
            for p in fil:
                prep = p.encounter_set\
                    .filter(encounter_date__gte=start-timedelta(days=365),\
                            encounter_date__lte=end,\
                            ccreport__pregnancyreport__encounter__encounter_date__gte=\
                                date(1900,01,01))\
                    .latest('encounter_date')\
                    .ccreport_set\
                    .filter(polymorphic_ctype__model='pregnancyreport')\
                    .latest('encounter__encounter_date')
               
                # Number of days since encounter
                days = (end - prep.encounter.encounter_date).days

                # Number of months since encounter
                months = round(days/30.4375)

                # If the pregnancy month plus months since encounter
                # is greater than 9 and there's no birth report,
                # then let's assume the lady is not pregnant
                months_pregnant = prep.pregnancy_month + months
                if months_pregnant > 9:
                    print 'too old %d in %s' % \
                        (prep.pregnancy_month, prep.encounter.encounter_date)
                    continue

                if not (months_pregnant >= start_month and \
                    months_pregnant <= end_month):
                    print 'not in right month...'
                    continue

                # Look for a baby since the pregnancy
                b = Patient\
                    .objects\
                    .filter(mother=p,\
                        dob__gte=end-timedelta(months_pregnant*30.4375),\
                        dob__lte=end)

                # If the birthreport has been found, then she's no longer
                # pregnant
                if b.count() > 0:
                    print 'birth at %d' % months_pregnant
                    continue

                # Look for a stillbirth/miscarriage
                sbm = p.encounter_set\
                    .filter(encounter_date__lte=end,
                        ccreport__stillbirthmiscarriagereport__incident_date__gte=\
                            end-timedelta(months_pregnant*30.4375),\
                        ccreport__stillbirthmiscarriagereport__incident_date__lte=\
                            end)\
               
                # If there was a stillbirth/misscariage, then she's
                # no longer pregnant
                if sbm.count() > 0:
                    print 'stillbirth'
                    continue
                
                print '*PR submitted %s at month %d (ago: %d)' % \
                    (prep.encounter.encounter_date, \
                        prep.pregnancy_month, months)
                pks.add(p.pk)
            f = fil.filter(pk__in=pks)
            return f
                 
        def pregnant_recently(self, start, end):
            raise NotImplementedError()

        def over_five_not_pregnant_recently(self, start, end):
            raise NotImplementedError()

        def delivered(self, start, end):
            raise NotImplementedError()


reversion.register(Patient)
