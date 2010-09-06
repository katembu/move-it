from django import template

from generator import Generator

class HTMLGenerator(Generator):
    def _start_document(self):
        self.sec_counter = 0
        self.para_counter = 0
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
        self.context["section_%d" % self.sec_counter,] = section.text
        self.tlines += u"<h3>{{section_%d}}</h3>\n" % self.sec_counter
        self.sec_counter += 1

    def _render_paragraph(self, paragraph):
        self.context["paragraph_%d" % self.para_counter,] = paragraph.text
        self.tlines += u"<p>{{paragraph_%d}}</p>\n" % self.para_counter
        self.para_counter += 1

    def _render_hline(self, hline):
        self.tlines += u"<hr />\n"

    def _end_document(self):
        self.tlines += u"</body>\n"
        self.tlines += u"</html>\n"

        ''' Compile template '''
        t = template.Template(''.join(self.tlines))
        ''' Compile context '''
        c = template.Context(self.context)
        self._handle.write(t.render(c))

        
