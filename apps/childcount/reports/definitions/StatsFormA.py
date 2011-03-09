
from django.utils.translation import gettext as _

from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Form A (Registration) per Day")
    filename = 'form_a_entered'
    formats = ['pdf','xls','html']

    def generate(self, rformat, title, filepath, data):
        return form_reporting(
            rformat,
            title,
            matching_message_stats(\
                [_(u"You successfuly registered ")]),
            filepath) 
            

