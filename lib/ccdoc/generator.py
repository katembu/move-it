import tempfile

from paragraph import Paragraph
from hline import HLine
from section import Section
from table import Table
from text import Text

class NotRenderedError(Exception):
    pass

class Generator(object):
    def __init__(self, document):
        self._handle = tempfile.NamedTemporaryFile()
        self._filename = self._handle.name

        self.title = document.title
        self.subtitle = document.subtitle
        self.contents = document.contents
        self._rendered = False

    def render_document(self):
        self._start_document()
        self._render_contents()
        self._end_document()
        self._rendered = True

    def _render_contents(self):
        obj = {}
        obj[Section] = self._render_section
        obj[Paragraph] = self._render_paragraph
        obj[HLine] = self._render_hline
        obj[Table] = self._render_table

        for c in self.contents:
            try:
                render_func = obj[type(c)]
            except KeyError:
                raise NotImplementedError("Cannot handle type: %s" % str(type(c)),) 
            render_func(c)
            
    def get_filename(self):
        if not self._rendered:
            raise NotRenderedError("Document not yet rendered")
        return self._handle.name

    def get_contents(self):
        if not self._rendered:
            raise NotRenderedError("Document not yet rendered")
        self._handle.seek(0)
        return self._handle.read()

    def destroy_file(self):
        return self._handle.close()


    ''' Rest of these must be implemented
        by generator inheritor classes
    '''

    def _start_document(self):
        raise NotImplementedError("Not implemented")

    def _end_document(self):
        raise NotImplementedError("Not implemented")

    def _render_paragraph(self, paragraph):
        raise NotImplementedError("Not implemented")

    def _render_table(self, table):
        raise NotImplementedError("Not implemented")

    def _render_section(self, section):
        raise NotImplementedError("Not implemented")

    def _render_hline(self, hline):
        raise NotImplementedError("Not implemented")

    def _render_table(self, table):
        raise NotImplementedError("Not implemented")
    
    def _render_text(self, text):
        raise NotImplementedError("Not implemented")
