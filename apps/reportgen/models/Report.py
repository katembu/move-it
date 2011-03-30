#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.db.models.signals import pre_save
from django.db import models, IntegrityError
from django.utils.translation import ugettext as _

class Report(models.Model):
    class Meta:
        app_label = 'reportgen'
        db_table = 'reportgen_report'
        verbose_name = _(u"Report")
        verbose_name_plural = _(u"Reports")
        ordering = ('title', )

    title = models.CharField(_(u"Title"), max_length=60, blank=False, \
                                null=False, db_index=True, unique=True, \
                                help_text=_(u"Human-readable title for report"))

    classname = models.CharField(_(u"Class name"), max_length=60, blank=False, \
                                null=False, db_index=True, unique=True, \
                                help_text=_(u"Name of module in which the report " \
                                            "is defined."))

    def __unicode__(self):
        return self.title

    def get_definition(self):
        return __import__(\
                ''.join(['reportgen.definitions.', self.classname]),
                globals(), locals(), ['Report'], -1).Report

def validate_report(sender, **kwargs):
    report = kwargs['instance']
    try:
        report.get_definition()
    except ImportError:
        raise IntegrityError(_("Could not import report definition "\
                                "named \"%s\".") % report.classname)

# Tell Django to run the custom validation logic
# on the Report before saving it
pre_save.connect(validate_report, \
    dispatch_uid='validate_report',
    sender=Report)

