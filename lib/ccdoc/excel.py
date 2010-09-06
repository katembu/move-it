from pyExcelerator import Workbook, XFStyle, Font

from generator import Generator

class ExcelGenerator(Generator):
    def _start_document(self):
        self.style = XFStyle()
        self.workbook = Workbook()

        self.sheets = [self.workbook.add_sheet(self.title)]
        self.cur_sheet = self.sheets[0]

        self.row = 0
        self.col = 0

        title_style = XFStyle()
        title_style.font.bold = True
        title_style.font.height = 500
        
        sub_style = XFStyle()
        sub_style.font.italic = True

        self.cur_sheet.write_merge( \
            self.row, self.row+1, \
            self.col, self.col+6, \
            self.title, title_style)
        self.row += 2

        if self.subtitle != None and self.subtitle != '':
            self.cur_sheet.write(self.row, self.col, \
                self.subtitle, sub_style)

    def _render_section(self, section):
        s = self.workbook.add_sheet(section.text)
        self.sheets.append(s)
        self.cur_sheet = s

    def _render_text(self, text):
        pass #self.cur_sheet.write(self.row, self.col, 

    def _render_paragraph(self, paragraph):
        self.cur_sheet.write(self.title)

    def _render_hline(self, hline):
        self.row += 1
        
    def _render_table(self, table):
        self.tlines += u"<table cellspacing=0>\n"
        
        if table.title != None: 
            self.tlines += u"<tr>\n"
            self.tlines += u"<th colspan='%d'>\n" % table.ncols,
            self.tlines += u"<h4>"
            self._render_text(table.title)
            self.tlines += u"</h4></th>"
       
        i=0
        ''' Iterate through each table row '''
        for row in table.rows:
            i += 1
            if i%2 == 0:
                odd = ''
            else:
                odd = ' class="odd"'
            self.tlines += u"<tr%s>\n" % odd

            ''' Iterate through each table column '''
            for col in row[1]:
                if row[0]: self.tlines += u"<th>"
                else: self.tlines += u"<td>"
               
                self._render_text(col)

                if row[0]: self.tlines += u"</th>"
                else: self.tlines += u"</td>"
            self.tlines += u"</tr>\n"
        self.tlines += u"</table>\n"

    def _end_document(self):
       self.workbook.save(self._filename) 
        
