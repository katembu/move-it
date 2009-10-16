#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date as pydate
from datetime import timedelta, datetime

from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from apps.reporters.models import *
from apps.locations.models import *

# CONFIGURATION
class Configuration(models.Model):

    id          = models.PositiveIntegerField(primary_key=True, default=1,editable=False)
    low_stock_level = models.PositiveIntegerField()

    def __unicode__(self):
        return "Configuration"

# EXCEPTIONS
class UnknownReporter(Exception):
    pass

class DuplicateReport(Exception):
    pass

class ErroneousDate(Exception):
    pass

class IncoherentValue(Exception):
    pass

class InvalidInput(Exception):
    pass

# REPORT PERIOD
class ReportPeriod(models.Model):

    class Meta:
        unique_together = ("start_date", "end_date")

    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField()

    def __unicode__(self):
        return _(u"%(weekfmt)s") % {'weeknum': self.week, 'weekfmt': self.formated}

    @property
    def week(self):
        return int(self.start_date.strftime("%W"))

    @property
    def date(self):
        return self.start_date

    @property
    def formated(self):
        return _(u"%s-%s") % (self.start_date.strftime("%d"), self.end_date.strftime("%d/%m/%y"))

    @classmethod
    def current(cls):
        today   = pydate.today()
        return cls.from_day(today)

    @classmethod
    def from_day(cls, day):
        start, end  = cls.weekboundaries_from_day(day)
        try:
            return cls.objects.get(start_date=start, end_date=end)
        except cls.DoesNotExist:
            # create it and return
            period  = cls(start_date=start, end_date=end)
            period.save()
            return period

    @classmethod
    def from_index(cls, index):
        if index == 0:
            return cls.current()
        elif index > 0:
            ref_day     = pydate.today() - timedelta(index * 7)
            return cls.from_day(ref_day)
        else:
            raise InvalidInput

    @classmethod
    def weekboundaries_from_day(cls, day):
        if day.weekday() < 6:
            # get previous week
            delta   = 7 + day.weekday()
            startd  = day - timedelta(delta)
            endd    = startd + timedelta(6)
            start   = datetime(startd.year, startd.month, startd.day)
            end     = datetime(endd.year, endd.month, endd.day, 23, 59)
            return (start, end)
        else:
            # sunday can't bind
            raise ErroneousDate

# FIND REPORT (GENERIC)
AUTHOR_SMS  = 0
AUTHOR_GUI  = 1
class FindReport:

    AUTHORS         = (
        (AUTHOR_SMS, _(u"SMS")),
        (AUTHOR_GUI, _(u"Graphical Interface")),
    )

    @property
    def author(self):
        return None

    @property
    def author_name(self):
        if self.last_edited_on:
            return None

# DISEASES
class Disease(models.Model):

    code    = models.CharField(max_length=2, unique=True)
    name    = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    @classmethod
    def by_code(cls, code):
        return cls.objects.get(code=code)

class DiseaseObservation(models.Model):

    class Meta:
        unique_together = ("disease", "cases", "deaths")

    disease = models.ForeignKey(Disease)
    cases   = models.PositiveIntegerField()
    deaths  = models.PositiveIntegerField()

    def __unicode__(self):
        #deathfmt  = _(u"+%(deaths)s") % {'deaths': self.deaths} if self.deaths > 0 else ""
        return _(u"%(code)s:%(cases)s/%(deaths)s") % {'code': self.disease.code.upper(), 'cases': self.cases, 'deaths': self.deaths}

    @classmethod
    def by_values(cls, disease, cases, deaths):
        try:
            return cls.objects.get(disease=disease, cases=cases, deaths=deaths)
        except cls.DoesNotExist:
            do = cls(disease=disease, cases=cases, deaths=deaths)
            do.save()
            return do

class DiseasesReport(models.Model,FindReport):

    TITLE       = _(u"Diseases Report")

    class Meta:
        unique_together = ("reporter", "period")

    reporter    = models.ForeignKey(Reporter)
    period      = models.ForeignKey(ReportPeriod)
    diseases    = models.ManyToManyField(DiseaseObservation, blank=True, null=True)
    sent_on     = models.DateTimeField(auto_now_add=True)
    edited_by   = models.ForeignKey(User, blank=True, null=True)
    edited_on   = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        cd  = self.cases_deaths
        return _(u"W%(week)s - %(clinic)s - %(cases)s+%(deaths)s") % {'week': self.period.week, 'clinic': self.reporter.location, 'cases': cd[0], 'deaths': cd[1]}

    @property
    def title(self):
        return self.TITLE

    @property
    def cases_deaths(self):
        cases   = 0
        deaths  = 0
        for obs in self.diseases.all():
            cases   += obs.cases
            deaths  += obs.deaths

        return cases, deaths

    @property
    def cases(self):
        return self.cases_deaths[0]

    @property
    def deaths(self):
        return self.cases_deaths[1]

    def reset(self):
        return self.diseases.clear()

    @classmethod
    def by_reporter_period(cls, reporter, period):
        try:
            return cls.objects.get(reporter=reporter, period=period)
        except cls.DoesNotExist:
            report  = cls(reporter=reporter, period=period)
            report.save()
            return report

# MALARIA CASES
class MalariaCasesReport(models.Model):

    class Meta:
        unique_together = ("reporter", "period")

    reporter    = models.ForeignKey(Reporter)
    period      = models.ForeignKey(ReportPeriod)

    encounters          = models.PositiveIntegerField(default=0)
    suspected_cases     = models.PositiveIntegerField(default=0)
    rdt_tests           = models.PositiveIntegerField(default=0)
    rdt_positive_tests  = models.PositiveIntegerField(default=0)
    microscopy_tests    = models.PositiveIntegerField(default=0)
    microscopy_positive = models.PositiveIntegerField(default=0)
    positive_under_five = models.PositiveIntegerField(default=0)
    positive_over_five  = models.PositiveIntegerField(default=0)

    sent_on     = models.DateTimeField(auto_now_add=True)
    edited_by   = models.ForeignKey(User, blank=True, null=True)
    edited_on   = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return _(u"W%(week)s - %(clinic)s") % {'week': self.period.week, 'clinic': self.reporter.location}

# MALARIA TREATMENTS
class MalariaTreatmentsReport(models.Model):

    class Meta:
        unique_together = ("reporter", "period")

    reporter    = models.ForeignKey(Reporter)
    period      = models.ForeignKey(ReportPeriod)

    rdt_positive        = models.PositiveIntegerField()
    rdt_negative        = models.PositiveIntegerField()
    four_months_to_three= models.PositiveIntegerField()
    three_to_seven      = models.PositiveIntegerField()
    seven_to_twelve     = models.PositiveIntegerField()
    twelve_and_above    = models.PositiveIntegerField()


    sent_on     = models.DateTimeField(auto_now_add=True)
    edited_by   = models.ForeignKey(User, blank=True, null=True)
    edited_on   = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return _(u"W%(week)s - %(clinic)s") % {'week': self.period.week, 'clinic': self.reporter.location}

# ACT CONSUMPTION
class ACTConsumptionReport(models.Model):

    class Meta:
        unique_together = ("reporter", "period")

    reporter    = models.ForeignKey(Reporter)
    period      = models.ForeignKey(ReportPeriod)

    yellow_used         = models.PositiveIntegerField()
    yellow_instock      = models.BooleanField()
    blue_used           = models.PositiveIntegerField()
    blue_instock        = models.BooleanField()
    brown_used          = models.PositiveIntegerField()
    brown_instock       = models.BooleanField()
    green_used          = models.PositiveIntegerField()
    green_instock       = models.BooleanField()
    quinine_used        = models.PositiveIntegerField()
    quinine_instock     = models.BooleanField()
    other_act_used      = models.PositiveIntegerField()
    other_act_instock   = models.BooleanField()

    sent_on     = models.DateTimeField(auto_now_add=True)
    edited_by   = models.ForeignKey(User, blank=True, null=True)
    edited_on   = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return _(u"W%(week)s - %(clinic)s") % {'week': self.period.week, 'clinic': self.reporter.location}

# EPIDEMIOLOGICAL REPORT
class EpidemiologicalReport(models.Model):

    STATUS_STARTED  = 0
    STATUS_COMPLETED= 1

    STATUSES        = (
        (STATUS_STARTED, _(u"Started")),
        (STATUS_COMPLETED, _(u"Completed")),
    )

    class Meta:
        unique_together = ("clinic", "period")

    clinic  = models.ForeignKey(Location, related_name='clinic')
    period  = models.ForeignKey(ReportPeriod, related_name='period')

    diseases            = models.ForeignKey(DiseasesReport, null=True, blank=True, related_name='diseases_report')
    malaria_cases       = models.ForeignKey(MalariaCasesReport, null=True, blank=True, related_name='cases_report')
    malaria_treatments  = models.ForeignKey(MalariaTreatmentsReport, null=True, blank=True, related_name='treatments_report')
    act_consumption     = models.ForeignKey(ACTConsumptionReport, null=True, blank=True, related_name='act_report')
    remarks             = models.CharField(max_length=160, blank=True, null=True)

    status      = models.CharField(max_length=1, choices=STATUSES,default=STATUS_STARTED)
    started_on  = models.DateTimeField(auto_now_add=True)
    completed_on= models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return _(u"W%(week)s - %(clinic)s - %(completion)s") % {'week': self.period.week, 'clinic': self.clinic, 'completion': self.quarters}

    @classmethod
    def by_clinic_period(cls, clinic, period):
        try:
            return cls.objects.get(clinic=clinic, period=period)
        except cls.DoesNotExist:
            report  = cls(clinic=clinic, period=period)
            report.save()
            return report

    @property
    def completion(self):
        comp    = 0
        if self.diseases:           comp += 0.25
        if self.malaria_cases:      comp += 0.25
        if self.malaria_treatments: comp += 0.25
        if self.act_consumption:    comp += 0.25

        return comp

    @property
    def quarters(self):
        comp    = self.completion
        stages  = 4
        return _(u"%(completed)s/%(total)s") % {'completed': int(comp * stages), 'total': int(stages)}

    def author(self):
        date = self.started_on
        for report in (self.diseases, self.cases, self.treats, self.act):
            if report.author:
                pass
        pass
        
