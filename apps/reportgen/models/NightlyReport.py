#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os
import os.path
from datetime import datetime

from django.db import models, IntegrityError
from django.db.models.signals import pre_save, pre_delete
from django.utils.translation import ugettext as _

from reportgen.timeperiods import PERIOD_CHOICES, PERIOD_TYPES

class NightlyReport(models.Model):
    NIGHTLY_DIR = 'nightly'

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
        raise IntegrityError(_("Time period code does not match " \
                                "any PeriodType object."))

    def period(self):
        return self.period_type().periods()[self.time_period_index]

    def time_period_current(self):
        return self\
            .period_type()\
            .periods()[self.time_period_index]\
            .title

    def time_period_str(self):
        return self\
            .period_type()\
            .periods()[self.time_period_index]\
            .relative_title

    def get_filename(self, variant, rformat):
        return self.report.get_filename(variant, rformat, self.pk)
    
    def get_filepath(self, variant, rformat):
        return os.path.join(\
            os.path.dirname(__file__),\
            '..',\
            'static',\
            self.NIGHTLY_DIR,\
            self.get_filename(variant, rformat))

    def get_filepaths(self):
        ps = []
        d = self.report.get_definition()

        # Get all report variant filename suffixes
        variants = [v[1] for v in d.variants]
        if len(variants) == 0:
            variants = [None]

        # Loop through all report filepaths
        for v in variants:
            for r in d.formats:
                ps.append(self.get_filepath(v,r))
        return ps

    def finished_at(self, variant, rformat):
        fname = self.get_filepath(variant, rformat)
        if not os.path.exists(fname):
            return None
        return datetime.fromtimestamp(os.path.getmtime(fname))

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

def delete_files(sender, **kwargs):
    nr = kwargs['instance']
    ps = nr.get_filepaths()
    print "All files |%s|" % ps
    for p in ps:
        if os.path.exists(p):
            print "Unlinking <%s>" % p
            os.unlink(p)
        else:
            print "Can't find <%s>" % p
    return True

# Tell Django to run the custom validation logic
# on the NightlyReport before saving it
pre_save.connect(validate_nightly_report, \
    dispatch_uid='validate_nightly_report',
    weak=False,
    sender=NightlyReport)

# Delete generated report files when you 
# delete this report from the DB
pre_delete.connect(delete_files,\
    dispatch_uid='delete_files',
    weak=False,
    sender=NightlyReport)
