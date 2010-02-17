#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

Commodity - Commodity model
'''

from django.db import models
from django.utils.translation import ugettext as _


class Commodity(models.Model):

    '''Commodity - Something that can be given to a patient
                   (medicine, bednet, etc...)
    '''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Commodity")
        verbose_name_plural = _(u"Commodities")

    code = models.CharField(_(u"Code"), max_length=10, unique=True)
    description = models.CharField(_(u"Description"), max_length=255)

    def __unicode__(self):
        return u'%(code)s - %(desc)s' % \
                {'code': self.code, 'desc': self.description}
