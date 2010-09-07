
from text import Text
from section import Section
from paragraph import Paragraph
from hline import HLine

class Document(object):
    def __init__(self, title, subtitle=''):
        self.title = title
        self.subtitle = subtitle
        self.contents = []

    def add_element(self, element):
        self.contents.append(element)

