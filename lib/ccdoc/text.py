

class Text(object):
    """ Generic text for document
        Later can contain font info, etc
    """

    DEFAULT_SIZE = 10

    def __init__(self, text, italic=False, bold=False,
            size=DEFAULT_SIZE):
        if isinstance(text, unicode):
            self.text = text
        if not isinstance(text, unicode):
            self.text = unicode(text)
           
        self.italic = italic
        self.bold = bold
        self.size = size

