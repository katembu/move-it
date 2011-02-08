#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from datetime import date

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group
from django.db.models import Sum

from reversion import revision
from reversion.models import Revision, Version

from locations.models import Location

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import send_msg
from childcount.exceptions import BadValue, ParseError
from childcount.models import BednetStock, DistributionPoints
from childcount.models import BednetIssuedReport


class LLNSummaryCommand(CCCommand):

    KEYWORDS = {
        'en': ['netsummary'],
        'fr': ['netsummary'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        '''if self.params.__len__() < 2:
            raise ParseError(_(u"Not enough information. Expected:"
                                "%(keyword)s | locationcode |" % \
                                {'keyword': self.params[0]}))
        try:
            loc = Location.objects.get(code__iexact=self.params[1])
        except Location.DoesNotExist:
            raise BadValue(_(u"Unknown location code %(loc)s." % \
                            {'loc': self.params[1]}))'''
        today = date.today()
        
        k = {}
        [k.update({dp.location: 0}) for dp in DistributionPoints.objects.all()]
        for bir in BednetIssuedReport\
            .objects\
            .filter(encounter__encounter_date__gte=today):
            d_sites = DistributionPoints.objects.filter(chw=bir.encounter.chw)
            distribution_site = None
            if d_sites:
                distribution_site = d_sites[0].location
            try:
                k[distribution_site] += bir.bednet_received
            except:
                print bir.encounter.chw
                continue

        _str = u''
        _jn = u''

        for item in k:
            bns = BednetStock.objects.get(created_on__day=today.day,
                created_on__month=today.month,
                created_on__year=today.year,
                location=item)
            remaining = bns.quantity
            print item, bns.quantity
            _str += _jn
            _str += u"%s:[start_point: %s, issued: %s, remaining: %s, "\
                "closing_point: %s]" % (item.__unicode__(),
                bns.start_point, k[item], remaining, bns.end_point)
            _jn = u', '
        self.message.respond(_str)
        # facilitators
        try:
            g = Group.objects.get(name='Facilitator')
            for user in g.user_set.all():
                try:
                    send_msg(user.reporter, _str)
                except:
                    print "Failed: ", user
        except Group.DoesNotExist:
                pass
        for dp in DistributionPoints.objects.all():
            for chw in dp.chw.all():
                inets = BednetIssuedReport.objects\
                    .filter(encounter__encounter_date__gte=today,
                    encounter__chw=chw)\
                    .aggregate(dc=Sum('bednet_received'))
                msg = _(u"You issued %s bednets on %s" % (inets['dc'],
                    today.strftime("%d/%m/%Y")))
                try:
                    send_msg(chw, msg)
                    send_msg(chw, _str)
                except:
                    print chw, msg
        return True
