#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

DangerSign - DangerSign store
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _


class DangerSign(models.Model):

    '''DangerSign store'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Danger Sign")
        verbose_name_plural = _(u"Danger Signs")

    code = models.CharField(_(u"Code"), max_length=10, unique=True)
    description = models.CharField(_(u"Description"), max_length=255)
