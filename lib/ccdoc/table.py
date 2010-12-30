
from text import Text

class TableDataError(Exception):
    pass

class InvalidRowError(TableDataError):
    pass

class InvalidCellError(TableDataError):
    pass


class Table(object):

    ALIGN_LEFT = 0
    ALIGN_RIGHT = 1
    ALIGN_CENTER = 2
    ALIGN_JUSTIFY = 3

    def __init__(self, ncols, title=None):
        ''' Optional: Text object -- title of table to be
            printed as a header over the table
        '''
        if title is not None:
            self.title = self._text_or_error(title)
        else:
            self.title = None

        ''' Number of columns in the table '''
        self.ncols = ncols

        ''' List of (bool, [col data]) tuples
            where bool indicates whether it's a 
            header row and data is the column
            contents.  The contents must be
            Text objects.
        '''
        self.rows = []

        self.column_widths = {}
        self.column_alignments = {}       

    def add_header_row(self, values):
        if len(values) != self.ncols:
            raise InvalidRowError
        values = map(self._text_or_error, values)
        self.rows.append((True, values))

    def add_row(self, values):
        if len(values) != self.ncols:
            raise InvalidRowError
        values = map(self._text_or_error, values)
        self.rows.append((False, values))

    def _text_or_error(self, obj):
        if not isinstance(obj, Text):
            raise InvalidCellError
        return obj

    def set_alignment(self, alignment, column):
        """ set alignment for a particular column/row """
        self.column_alignments[column] = alignment

    def set_column_width(self, width, column):
        """ set width (in % of total) of a particular column """
        self.column_widths[column] = width
