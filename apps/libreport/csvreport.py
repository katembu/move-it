import os
import csv
import StringIO
from datetime import datetime

from django.template import Template, Context
from django.http import HttpResponse



class CSVReport():
    '''
    CSVReport Is a class that creates raw CSV reports::

        csvrpt = PDFRreport()
        csvrpt.setLandscape(False)
        csvrpt.setTitle("Title")
        csvrpt.setTableData(queryset, fields, "Table Title")
        csvrpt.setFilename("filename")
        csvrpt.render()

    '''
    title = "Report"
    filename = "report"

    pageinfo = None
    styles = None
    landscape = None
    hasfooter = None
    headers = None
    cols = None
    PAGESIZE = None
    fontSize = None

    def __init__(self):
        self.output = StringIO.StringIO()
        self.csvio = csv.writer(self.output)
        self.data = []

    # compatibility with PDFReport
    def setLandscape(self, state):
        pass

    def enableFooter(self, state):
        pass

    def setTitle(self, title):
        pass

    def setPageInfo(self, pageinfo):
        pass

    def setFontSize(self, size):
        pass

    def setNumOfColumns(self, cols):
        pass

    def setFilename(self, filename):
        """
        :param filename: filename for the generated pdf document
        """
        if filename:
            self.filename = filename

    def setPageBreak(self):
        """force a page break
        """
        self.data.append("")


    def setTableData(self, queryset, fields, title):
        """set table data

        :param queryset: data
        :param fields: table column headings
        :param title: Table Heading
        """
        header = False

        for row in queryset:
            if not header:
                self.data.append([f["name"] for f in fields])
                header = True
            ctx = Context({"object": row})
            values = [Template(h["bit"]).render(ctx) for h in fields]
            self.data.append(values)

    def render(self):
        filename = self.filename + datetime.now().strftime("%Y%m%d%H%M%S")\
                 + ".csv"
        for data in self.data:
            self.csvio.writerow(data)
        response = HttpResponse(mimetype='text/csv')
        response['Cache-Control'] = ""
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        response.write(self.output.getvalue())
        return response
