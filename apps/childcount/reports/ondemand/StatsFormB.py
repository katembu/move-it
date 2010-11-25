
from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Form B Entered by Day'
    filename = 'form_b_entered'
    formats = ['pdf','xls','html']
    argvs = []

    def generate(self, rformat, **kwargs):
        return form_reporting(
            rformat,
            u'Form B (HH Visit) Per Day',
            matching_message_stats(\
                ' `text` LIKE "%%+V%% Successfully processed: [%%" \
                AND `backend` = "debackend" '),
            self.get_filepath(rformat))


