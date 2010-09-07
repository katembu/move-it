
from text import Text

class Paragraph(object):
    '''
        A paragraph represents a single paragraph in a document.
        It can either be a single string, or a list of Text objects
        if you want the paragraph to have different styles within
        the same block of text.

        Examples:
            Paragraph(u'My first sentence.  My second sentence.')
            Paragraph(Text('My bold paragraph', bold=True))
            Paragraph([
                Text('Bold sentence. ', bold=True),
                Text('Italic sentence. ', italic=True)])

    '''

    def __init__(self, text):
        if isinstance(text, str) or isinstance(text, unicode):
            self.contents = [Text(text)]
        elif isinstance(text, Text):
            self.contents = [text]
        elif isinstance(text, list):
            self.contents = text
        else:
            raise ValueError('Invalid arg')
            

