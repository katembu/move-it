#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Should contain location related models

Clinic
Zone
'''

from django.utils.translation import ugettext_lazy as _

from locations.models import Location

class Clinic(Location):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Clinic")
        verbose_name_plural = _(u"Clinics")
    pass
