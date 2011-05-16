#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.utils.translation import gettext as _

from childcount.models.reports import NutritionReport

def latest_muac_raw(period, p):
    try:
        n = NutritionReport\
            .objects\
            .filter(encounter__patient=p, \
                encounter__encounter_date__lte=period.end,
                muac__isnull=False,
                muac__gt=0).latest()
    except NutritionReport.DoesNotExist:
        return None
    return n

def latest_muac_date(period, p):
    n = latest_muac_raw(period, p)
    if n is None:
        return _(u"[No MUAC]")
    
    ''' Oed = Oedema '''
    return _(u"%(date)s [%(muac)s,Oed:%(oedema)s]") % \
        {'date': n.encounter.encounter_date.strftime('%d %b %Y'),
        'muac': n.muac or '--',
        'oedema': n.oedema}

def latest_muac(period, p):
    muac = latest_muac_raw(period, p)
    if muac is not None:
        return u"%smm %s" % (muac.muac, muac.verbose_state)
    return u""


