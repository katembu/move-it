#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.db import models, IntegrityError
from django.db.models.signals import pre_save
from django.utils.translation import ugettext as _

from reportgen.timeperiods import PERIOD_CHOICES, PERIOD_TYPES

class NightlyReport(models.Model):

    class Meta:
        app_label = 'reportgen'
        db_table = 'reportgen_nightly_report'
        verbose_name = _(u"Nightly Report")
        verbose_name_plural = _(u"Nightly Reports")
        ordering = ('report__title', )

    report = models.ForeignKey('Report', max_length=60, blank=False, \
                                verbose_name=_(u"Report"),
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Reference to the report "\
                                    "to be generated overnight"))
    time_period = models.CharField(_(u"Time period"), max_length=2, blank=False, \
                                null=False, db_index=True, unique=False, \
                                choices=PERIOD_CHOICES,
                                help_text=_(u"The time period type to use"))
    time_period_index = models.PositiveSmallIntegerField(_(u"Class name"), \
                                blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Index of period with which to generate "\
                                            "this report"))
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s [%s: Starting %s]" % (self.report, \
                self.period_type().title, self.time_period_str())

    def period_type(self):
        for p in PERIOD_TYPES:
            if p.code == self.time_period:
                return p
        return IntegrityError(_("Time period code does not match " \
                                "any PeriodType object."))

    def time_period_str(self):
        return self\
            .period_type()\
            .periods()[self.time_period_index]\
            .relative_title

def validate_nightly_report(sender, **kwargs):
    rep = kwargs['instance']
    pt = rep.period_type()
    if rep.time_period_index not in xrange(0, pt.n_periods):
        raise IntegrityError(_("PeriodType \"%(pt)s\" only has "\
                                "%(n)d periods. You told me to "\
                                "generate a report for period %(m)d.") % \
                    {'pt': pt.title, \
                    'n': pt.n_periods, \
                    'm': rep.time_period_index})

# Tell Django to run the custom validation logic
# on the NightlyReport before saving it
pre_save.connect(validate_nightly_report, \
    dispatch_uid='validate_nightly_report',
    sender=NightlyReport)
