import tempfile

from paragraph import Paragraph
from hline import HLine
from section import Section
from table import Table

class NotRenderedError(Exception):
    pass

class Generator(object):
    def __init__(self, document):
        self._handle = tempfile.NamedTemporaryFile()

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
        obj[type(Section)] = self._render_section
        obj[type(Paragraph)] = self._render_paragraph
        obj[type(HLine)] = self._render_hline
        obj[type(Table)] = self._render_table

        for c in self.contents:
            object[type(c)]()

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
    
        
