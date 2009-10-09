import os
from datetime import datetime
from django.template import Template, Context
from django.http import HttpResponse, HttpResponseRedirect

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, CondPageBreak
    from reportlab.platypus import Table as PDFTable
    from reportlab.platypus import TableStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors 
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.rl_config import defaultPageSize
    from reportlab.lib.units import inch
    PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
except ImportError:
    pass

''' PDFReport Is a class that create table format reports
    usage: 
            pdfrpt = GenPDFRrepot()
            pdfrpt.setLandscape(False)
            pdfrpt.setTitle("Title")
            pdfrpt.setTableData(queryset, fields, "Table Title")
            pdfrpt.setFilename("filename")
            pdfrpt.render()
'''

class PDFReport():
    title = "Report"
    pageinfo = ""
    filename = "report"
    styles = getSampleStyleSheet()
    data = []
    landscape = False
    hasfooter = False
    
    # enable or disable landscape display
    # @var state: True or False
    def setLandscape(self, state):
        self.landscape = state

    # enable formatter for the last row of the table
    # e.g for summaries have bold border lines
    # @var state: True or False
    def enableFooter(self, state):
        self.hasfooter = state
        
    # @var title: The Report Title
    def setTitle(self, title):
        if title:
            self.title = title
           
    def setPageInfo(self, pageinfo):
        if pageinfo:
            self.pageinfo = pageinfo

    # @var filename: filename for the generated pdf document           
    def setFilename(self, filename):
        if filename:
            self.filename = filename
            
    # force a page break 
    def setPageBreak(self):
        self.data.append(PageBreak())
         
    # set table data
    # @var queryset: data
    # @var fields: table column headings
    # @var title: Table Heading
    def setTableData(self, queryset, fields, title):        
        self.data.append(Paragraph("%s" % title, self.styles['Heading3']))
        data = []
        header = False
        
        #prepare the data
        for row in queryset:
            if not header:
                data.append([f["name"] for f in fields])
                header = True
            ctx = Context({"object": row })
            values = [ Template(h["bit"]).render(ctx) for h in fields ]
            data.append(values)
        
        table = PDFTable(data,None,None,None,1)
        #table rows n cols formatting
        ts = [
            ('ALIGNMENT', (0,0), (-1,-1), 'LEFT'),
            ('LINEBELOW', (0,0), (-1,-0), 2, colors.black),            
            ('LINEBELOW', (0,1), (-1,-1), 0.8, colors.lightgrey),
            ('FONT', (0,0), (-1, -1), "Times-Roman", 8),
            ('ROWBACKGROUNDS', (0,0), (-1, -1), [colors.whitesmoke, colors.white]),            
        ]
        
        #last row formatting when required
        if self.hasfooter is True:
            ts.append(('LINEABOVE', (0,-1), (-1,-1), 1, colors.black))
            ts.append(('LINEBELOW', (0,-1), (-1,-1), 2, colors.black))
            ts.append(('LINEBELOW', (0,3), (-0,-0), 2, colors.green))             
            ts.append(('LINEBELOW', (0,-1), (-1,-1), 0.8, colors.lightgrey))
            ts.append(('FONT', (0,-1), (-1, -1), "Times-Roman", 8))
            
        table.setStyle(TableStyle(ts))

        table.hAlign = "LEFT"
        self.data.append(table)
        
    def render(self):
        elements = []
        
        self.styles['Title'].alignment = TA_LEFT
        self.styles['Title'].fontName = self.styles['Heading2'].fontName = "Times-Roman"
        self.styles["Normal"].fontName = "Times-Roman"
        self.styles["Normal"].fontSize = 10
        #self.styles["Normal"].fontWeight = "BOLD"
            
        filename = self.filename + datetime.now().strftime("%Y%m%d%H%M%S") + ".pdf"
        doc = SimpleDocTemplate(filename)
        
        elements.append(Paragraph(self.title, self.styles['Title']))
        
        for data in self.data:
            elements.append(data)
                
        if self.landscape is True:
            doc.pagesize = landscape(A4)
        
        doc.build(elements, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
        
        response = HttpResponse(mimetype='application/pdf')
        response['Cache-Control'] = ""
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        response.write(open(filename).read())
        os.remove(filename)
        return response
        
    # what should appear on the first page 
    def myFirstPage(self, canvas, doc):
        pageinfo = self.pageinfo
        canvas.saveState()
        '''canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
        '''
        textobject = canvas.beginText()
        textobject.setTextOrigin(inch, 0.75*inch)
        textobject.setFont("Times-Roman", 9)
        textobject.textLine("Page %d" % (doc.page))
        textobject.setFillGray(0.4)
        textobject.textLines(pageinfo)
        canvas.hAlign = "CENTER"
        canvas.drawText(textobject)
        canvas.restoreState()
    
    # what to do on other pages
    def myLaterPages(self, canvas, doc):
        pageinfo = self.pageinfo
        canvas.saveState()
        '''canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
        '''
        textobject = canvas.beginText()
        textobject.setTextOrigin(inch, 0.75*inch)
        textobject.setFont("Times-Roman", 9)
        textobject.textLine("Page %d" % (doc.page))
        textobject.setFillGray(0.4)
        textobject.textLines(pageinfo)
        canvas.hAlign = "CENTER"
        canvas.drawText(textobject)
        canvas.restoreState()

