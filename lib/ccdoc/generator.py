import os
import time
import tempfile

from django.utils.translation import ugettext as _

import bonjour.dates

from paragraph import Paragraph
from hline import HLine
from section import Section, PageBreak
from table import Table
from text import Text

class NotRenderedError(Exception):
    pass

class Generator(object):
    def __init__(self, document, filename = None):
        self.user_file = filename is not None
        if filename is not None:
            try:
                self._handle = open(filename, 'w')
            except IOError as e:
                raise IOError(_("Could not open file <%s>" % filename))
            self._filename = filename
        else:
            self._handle = tempfile.NamedTemporaryFile(delete=False)
            self._filename = self._handle.name
        
        self.document = document
        self.title = document.title
        self.subtitle = document.subtitle
        self.landscape = document.landscape
        self.stick_sections = document.stick_sections
        if document.datestring:
            self.datestring = bonjour.dates.format_datetime(format='full')
        else:
            self.datestring = u""
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
        obj[PageBreak] = self._render_pagebreak

        for c in self.contents:
            try:
                render_func = obj[type(c)]
            except KeyError:
                raise NotImplementedError("Cannot handle type: %s" % \
                    str(type(c)),) 
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

    def close_file(self):
        self._handle.close()

    def destroy_file(self):
        self._handle.close()
        os.unlink(self._handle.name)


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

    def _render_pagebreak(self, pagebreak):
        raise NotImplementedError("Not implemented")

    def _render_table(self, table):
        raise NotImplementedError("Not implemented")
    
    def _render_text(self, text):
        raise NotImplementedError("Not implemented")
