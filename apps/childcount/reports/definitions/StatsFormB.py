
from django.utils.translation import gettext as _

from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Form B (HH Visit) per Day")
    filename = 'form_b_entered'
    formats = ['pdf','xls','html']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        return form_reporting(
            rformat,
            title,
            matching_message_stats(\
                ' `text` LIKE "%%+V%% ' + _(u"Successfully processed: [") + '%%" \
                AND `backend` = "debackend" '),
            filepath)

