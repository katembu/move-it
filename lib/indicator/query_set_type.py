
class QuerySetType(object):
    mtype = None
    def __init__(self, mtype):
        self.mtype = mtype

    def __str__(self):
        return "QuerySet(%s)" % self.mtype.__name__

