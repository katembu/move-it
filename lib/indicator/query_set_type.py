
class QuerySetType(object):
    """ :class:`QuerySetType` is a bogus
    type just used with :class:`indicator.indicator.Indicator`
    definitions to specify the particular model type of the
    :class:`QuerySet` it accepts as an input argument.

    This is not duck-typing and it makes me feel dirty.
    Let's figure out a better way to do this.
    """

    mtype = None
    def __init__(self, mtype):
        self.mtype = mtype

    def __str__(self):
        return "QuerySet(%s)" % self.mtype.__name__

    def __eq__(self, other):
        return self.mtype == other.mtype

    def __neq__(self, other):
        return not self.__eq__(other)


