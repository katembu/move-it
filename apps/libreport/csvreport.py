import os
from datetime import datetime
from django.template import Template, Context
from django.http import HttpResponse, HttpResponseRedirect

import os
import csv
import StringIO

''' CSVReport Is a class that create raw CSV reports
 
            csvrpt = PDFRreport()
            csvrpt.setLandscape(False)
            csvrpt.setTitle("Title")
            csvrpt.setTableData(queryset, fields, "Table Title")
            csvrpt.setFilename("filename")
            csvrpt.render()
'''

class CSVReport():
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
        self.csvio  = csv.writer(self.output)
        self.data   = []
    
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

    # @var filename: filename for the generated pdf document           
    def setFilename(self, filename):
        if filename:
            self.filename = filename
            
    # force a page break 
    def setPageBreak(self):
        self.data.append("")
         
    # set table data
    # @var queryset: data
    # @var fields: table column headings
    # @var title: Table Heading
    def setTableData(self, queryset, fields, title):        

        header = False
        
        for row in queryset:
            if not header:
                self.data.append([f["name"] for f in fields])
                header = True
            ctx = Context({"object": row })
            values = [ Template(h["bit"]).render(ctx) for h in fields ]
            self.data.append(values)

        
    def render(self):
            
        filename = self.filename + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv"
                
        for data in self.data:
            self.csvio.writerow(data)
        
        response = HttpResponse(mimetype='text/csv')
        response['Cache-Control'] = ""
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        response.write(self.output.getvalue())
        return response
        
  
