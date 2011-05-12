from datetime import datetime, date

from hashlib import sha1

from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

STR_FUNCTIONS = {
    int:            str,
    float:          str,
    datetime:       str,
    date:           str,
    bool:           str,
}

def _filter_cache_key(func, self, args, kwargs):
    hvals = []

    try:
        for i, a in enumerate(args):
            to_str = STR_FUNCTIONS[type(a)]
            hvals.append("%d-%s" % (i, to_str(a)))

        for k in kwargs:
            to_str_k = STR_FUNCTIONS[type(k)]
            to_str_v = STR_FUNCTIONS[type(kwargs[k])]
            hvals.append("%s:%s" % (to_str_k(k), to_str_v(kwargs[v])))
    except KeyError as e:
        raise ValueError(_("Cannot cache function with an argument "\
            "of type %s" % e))

    print hvals
    hvals += self.to_list()
    s = sha1()
    for h in hvals:
        s.update(h)

    return s.hexdigest()

def cache_filter(func, timeout=(5)):
    def x(self, *args, **kwargs):
        # Calculate the cache key for this QuerySet
        cache_key = _filter_cache_key(func, self, args, kwargs)

        # Look for the value in the cache
        cached = cache.get(cache_key)

        # QuerySet value is in the cache
        if cached is not None:
            print "Got cached value!"
            # Cached value is a list of pks
            out = self.filter(pk__in=cached)
            return out
            
        # QuerySet value is not in the cache
        # Generate the value
        qset = func(self, *args, **kwargs)
        if qset is None:
            raise ValueError(_("Cannot cache function that returns a value "\
                                "of None"))

        # Convert the QuerySet into something pickleable
        cache_val = qset.pk_list()
        print cache_val
        cache.set(cache_key, cache_val, timeout)

        return qset
    return x
