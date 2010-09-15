
from text import Text

class Section(Text):
    ''' Section is a section heading...

        You cannot modify the style of a section
        heading -- you can only pass it a string
        for a title.
    '''

    def __init__(self, text):
        Text.__init__(self, text)

