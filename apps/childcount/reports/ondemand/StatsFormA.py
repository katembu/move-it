
from childcount.reports.statistics import form_reporting, matching_message_stats
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Form A (Registration) per Day'
    filename = 'form_a_entered'
    formats = ['pdf','xls','html']

    def generate(self, rformat, title, filepath, data):
        return form_reporting(
            rformat,
            title,
            matching_message_stats(\
                ['You successfuly registered ']),
            filepath) 
            

