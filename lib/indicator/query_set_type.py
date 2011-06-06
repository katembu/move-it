
class QuerySetType(object):
    mtype = None
    def __init__(self, mtype):
        self.mtype = mtype

    def __str__(self):
        return "QuerySet(%s)" % self.mtype.__name__

    def __eq__(self, other):
        return self.mtype == other.mtype

    def __neq__(self, other):
        return not self.__eq__(other)


