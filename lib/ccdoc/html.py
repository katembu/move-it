from django import template

from generator import Generator

class HTMLGenerator(Generator):
    def _start_document(self):
        self.var_counter = 0
        self.context = {}
        self.tlines = []

        self.tlines += u"<html>\n"
        self.tlines += u"<head>\n"

        self.tlines += u"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"

        self.tlines += \
        '''
            <style type="text/css">
                body {
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 0.8em;
                    min-width: 750px;
                    border: 1px solid #eee;
                    padding: 2em;
                }

                th.tabtitle {
                    font-size: 1.2em;
                    border-bottom: 1px solid #000;
                }

                h1 {
                    margin-bottom: 0px;
                }

                h2 {
                    margin-top: 2em;
                    border-top: 1px solid #ccc;
                    padding-top: 1em;
                }

                h5 {
                    margin-top: 0px;
                }
                
                table {
                    cellspacing: 0;
                    font-size:0.9em;
                    width: 750px;
                }

                table th {
                    border-bottom: 1px solid #000;
                }

                table th {
                    min-width:100px;
                    text-align: center;
                }

                table td {
                    text-align: left;
                }

                table tr.odd td {
                    background-color: #eee;
                }
            </style>
        '''

        self.context['title'] = self.title
        
        self.tlines += u"<title>{{title}}</title>\n"
        self.tlines += u"</head>\n<body>\n"
        self.tlines += u"<h1>{{title}}</h1>\n"
        self.tlines += self.datestring
        
        if self.subtitle != None and self.subtitle != '':
            self.context['subtitle'] = self.subtitle
            self.tlines += u"<h5><em>{{subtitle}}</em></h5>\n"

    def _render_section(self, section):
        self.tlines += u"<h2>\n"
        self._render_text(section)
        self.tlines += u"</h2>\n" 

    def _render_pagebreak(self, pagebreak):
        self.tlines += u"<div style='page-break-after:always;'>\n"
        self.tlines += u"<br />&nbsp;"
        self.tlines += u"</div'>\n"

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
        self.tlines += u"<table cellspacing=0>\n"
        
        if table.title != None: 
            self.tlines += u"<tr>\n"
            self.tlines += u"<th colspan='%d' class='tabtitle'>\n" % table.ncols,
            self._render_text(table.title)
            self.tlines += u"</th>"
       
        i=1
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
        self.tlines += u"</body>\n"
        self.tlines += u"</html>\n"
        
        ''' Compile template '''
        t = template.Template(''.join(self.tlines))
        ''' Compile context '''
        c = template.Context(self.context)
        self._handle.write(t.render(c).encode('utf-8'))       
