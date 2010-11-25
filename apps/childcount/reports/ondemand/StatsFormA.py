
from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Form A Entered by Day'
    filename = 'form_a_entered'
    formats = ['pdf','xls','html']

    def generate(self, rformat, **kwargs):
        return form_reporting(
            rformat,
            u'Form A Registrations Per Day',
            matching_message_stats(\
                ['You successfuly registered ']),
            self.get_filepath(rformat))
            


