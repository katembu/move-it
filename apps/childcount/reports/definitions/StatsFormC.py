
from django.utils.translation import gettext as _

from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Form C (Consultation) per Day")
    filename = 'form_c_entered'
    formats = ['pdf','xls','html']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        return form_reporting(
            rformat,
            title,
            matching_message_stats(\
                ' `text` LIKE "%%+U %%" OR \
                  `text` LIKE "%%+S %%" OR \
                  `text` LIKE "%%+P %%" OR \
                  `text` LIKE "%%+N %%" OR \
                  `text` LIKE "%%+T %%" OR \
                  `text` LIKE "%%+M %%" OR \
                  `text` LIKE "%%+F %%" OR \
                  `text` LIKE "%%+G %%" OR \
                  `text` LIKE "%%+R %%" AND \
                `text` LIKE "%%' + _(u"Successfully processed: [") + '%%%%" AND \
                `backend` = "debackend" '),
                filepath)
