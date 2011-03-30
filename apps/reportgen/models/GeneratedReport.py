#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.db import models
from django.utils.translation import ugettext as _

class GeneratedReport(models.Model):

    class Meta:
        app_label = 'reportgen'
        db_table = 'reportgen_generated_report'

        verbose_name = _(u"Generated Report")
        verbose_name_plural = _(u"Generated Reports")
        ordering = ('title', )

    filename = models.CharField(_(u"Filename"), max_length=255, blank=False, \
                                null=False, db_index=True, unique=True, \
                                help_text=_(u"Location of generated report file"))
    title = models.CharField(_(u"Title"), max_length=255, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Full title of report"))
    fileformat = models.CharField(_(u"File format"), max_length=10, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"File format of report (e.g., PDF)"))
    period_title = models.CharField(_(u"Period title"), max_length=100, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Description of the time period for "\
                                            "the report (e.g., \"January 2011\""))
    variant_title = models.CharField(_(u"Variant title"), max_length=100, blank=False, \
                                null=False, db_index=True, unique=False, \
                                help_text=_(u"Description of the variant for "\
                                            "the report (e.g., \"Ntungu Clinic\""))
    started_at = models.DateTimeField(_("Started at"))
    finished_at = models.DateTimeField(_("Finished at"))
    error_message = models.TextField(_("Error message"))
    updated_on = models.DateTimeField(auto_now=True)

