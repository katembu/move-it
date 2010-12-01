
def print_func(val):
    out = None
    try:
        out = int(val)
    except ValueError:
        pass

    if out is None:
        try:
            out = float(val)
        except ValueError:
            pass

    if out is None:
        print "string: %s" % val
        out = unicode(val)
    return out

class Indicator(object):
    _agg_func = None
    _for_week = None
    _print_func = None
    title = None

    EMPTY_FUNC = lambda n: ''
    EMPTY = ('________', EMPTY_FUNC, EMPTY_FUNC) 

    def __init__(self, title, for_week, agg_func, print_func=print_func):
        self.title = title
        self._agg_func = agg_func
        self._for_week = for_week
        self._print_func = print_func

    def _for_month(self):
        return self._agg_func([self._for_week(w) for w in xrange(0,4)])

    def for_month(self):
        return self._print_func(self._for_month())

    def for_week(self, week_num):
        return self._print_func(self._for_week(week_num))
