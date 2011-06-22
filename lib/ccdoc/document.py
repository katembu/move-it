
from django.utils.translation import ugettext_lazy as _

from text import Text
from section import Section
from paragraph import Paragraph
from hline import HLine

class Document(object):
    ''':class:`Document` holds the entire report to be
    generated and is what you pass to a
    Generator object.

    Besides setting the title and subtitle
    the only thing you need to do is add
    elements (:class:`ccdoc.paragraph.Paragraph`, 
    :class:`ccdoc.section.Section`, :class:`ccdoc.table.Table`) to
    it.
    '''

    def __init__(self,
            title,
            subtitle=None,
            landscape=False,
            stick_sections=False,
            datestring=True):
        """
        
        """

        self.title = title
        self.subtitle = subtitle
        self.landscape = landscape
        self.stick_sections = stick_sections
        self.datestring = datestring
        self.contents = []

    def add_element(self, element):
        """Add an element to the document object"""
        self.contents.append(element)

