from generator import Generator

class ReportLabGenerator(Generator):
    def _start_document(self):
        self.var_counter = 0
        self.context = {}
        self.tlines = []

        self.tlines += u"<html>\n"
        self.tlines += u"<head>\n"

        self.context['title'] = self.title
        
        self.tlines += u"<title>{{title}}</title>\n"
        self.tlines += u"</head>\n<body>\n"
        self.tlines += u"<h1>{{title}}</h1>\n"

        if self.subtitle != None and self.subtitle != '':
            self.context['subtitle'] = self.subtitle
            self.tlines += u"<h2>{{subtitle}}</h2>\n"

    def _render_section(self, section):
        self.tlines += u"<h3>\n"
        self._render_text(section)
        self.tlines += u"</h3>\n" 

    def _render_text(self, text):
        self.context["text_%d" % self.var_counter] = text.text
        if text.bold:
            self.tlines += "<strong>"
        if text.italic:
            self.tlines += "<em>"
        if text.size != text.DEFAULT_SIZE:
            self.tlines += "<font style='font-size:%dpx'>" % text.size

        self.tlines += u"{{ text_%d }}" % self.var_counter,
        self.var_counter += 1

        
        if text.size != text.DEFAULT_SIZE:
            self.tlines += "</font>"
        if text.italic:
            self.tlines += "</em>"
        if text.bold:
            self.tlines += "</strong>"
        
    def _render_paragraph(self, paragraph):
        self.tlines += u"<p>\n"
        for p in paragraph.contents:
            self._render_text(p)
        self.tlines += u"</p>\n"

    def _render_hline(self, hline):
        self.tlines += u"<hr />\n"

    def _render_table(self, table):
        self.tlines += u"<table>\n"
        
        if table.title != None: 
            self.tlines += u"<tr>\n"
            self.tlines += u"<th colspan='%d'>\n" % table.ncols,
            self.tlines += u"<h4>"
            self._render_text(table.title)
            self.tlines += u"</h4></th>"
        
        ''' Iterate through each table row '''
        for row in table.rows:
            self.tlines += u"<tr>\n"

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
        self.tlines += u"</body>\n"
        self.tlines += u"</html>\n"
        
        ''' Compile template '''
        t = template.Template(''.join(self.tlines))
        ''' Compile context '''
        c = template.Context(self.context)
        self._handle.write(t.render(c))

        
