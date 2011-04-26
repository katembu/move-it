#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import fractions

from django.utils.translation import ugettext as _

class Percentage(fractions.Fraction):
    """
    This is exactly like fractions.Fraction except
    that Percentage never simplifies the numerator
    or denominator.
    """

    num = 0
    den = 1
    empty = False

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return "%s (%d/%d)" % (self.short_str(), self.num, self.den)

    def short_str(self):
        return u'--' if empty else (u"%d%%" % int(self))

    def __new__(cls, n, d):
        empty = (d == 0)
        obj = super(Percentage,cls).__new__(cls, n, 1 if empty else d)
        obj.num = n
        obj.den = d
        obj.empty = empty

        return obj


