
import cPickle

from datetime import datetime, date

from hashlib import sha1

from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

from percentage import Percentage
from query_set_type import QuerySetType

"""A mapping of a type => function to
use to turn an object of this type
into a cache key
"""
STR_FUNCTIONS = {
    int:            str,
    float:          str,
    datetime:       str,
    date:           str,
    bool:           str,
    dict:           str,
}

"""Indicator output types that can be cached."""
CACHEABLE_TYPES = (int, float, datetime, \
    date, bool, Percentage, dict)

def _filter_cache_key(func, self, args, kwargs):
    hvals = []

    # Convert the input arguments into cacheable
    # values
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
            return self.filter(pk__in=cached)
            
        # QuerySet value is not in the cache
        # so generate the value
        qset = func(self, *args, **kwargs)
        if qset is None:
            raise ValueError(_("Cannot cache function that returns a value "\
                                "of None"))

        # Get the pks in this queryset and pickle them
        cache_val = qset.pk_list()
        print cache_val
        cache.set(cache_key, cache_val, timeout)

        return qset
    return x

def cache_indicator(cls, ind_func, period, data_in):
    # First, make sure we want to execute the caching logic
    if not cls.cache:
        return ind_func(period, data_in)

    if not cls.type_out in CACHEABLE_TYPES:
        raise TypeError(_("Indicator with output type %s cannot be cached") % \
                        str(cls.type_out))


    # Get the cache key from the function and arguments
    cache_key_elms = [str(cls), cls.slug, \
        str(period.start), str(period.end)]

    if isinstance(cls.type_in, QuerySetType):
        cache_key_elms.append("QuerySet")
        cache_key_elms.append(str(type(data_in)))
        cache_key_elms.append(str(data_in.model))
   
        cache_key_elms += [str(p[0]) for p in \
            data_in.order_by('pk').values_list('pk')]

    else:
        cache_key_elms.append("Other")

        func = STR_FUNCTIONS[cls.type_in]
        cache_key_elms.append(func(data_in))

    s = sha1()
    for e in cache_key_elms:
        s.update(e)

    cache_key = s.hexdigest()

    # Look for a cached value
    cached = cache.get(cache_key)
    if cached is not None:
        print "Got cached indicator"
        return cached

    
    cache_val = ind_func(period, data_in)
    if cache_val is None:
        raise ValueError(_("Cannot cache function that returns a value "\
                            "of None"))

    cache.set(cache_key, cache_val, cls.valid_for)

    return cache_val

