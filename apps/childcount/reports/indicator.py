
class Indicator(object):
    _agg_func = None
    _for_week = None
    _print_func = None
    title = None

    def __init__(self, title, for_week, agg_func, print_func=lambda a:a):
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
