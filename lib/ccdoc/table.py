
from text import Text

class InvalidRowError(Exception):
    pass

class Table(object):
    def __init__(self, ncols, title=None):
        self.title = title
        self.ncols = ncols

        ''' List of (bool, [col data]) tuples
            where bool indicates whether it's a 
            header row and data is the column
            contents
        '''
        self.rows = []

    def add_header_row(self, values):
        if len(values) != self.ncols:
            raise InvalidRowError
        self.rows.append((True, values))

    def add_row(self, values):
        if len(values) != self.ncols:
            raise InvalidRowError
        self.rows.append((False, values))


