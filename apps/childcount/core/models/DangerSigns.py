#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

DangerSigns - DangerSigns store
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _


class DangerSigns(models.Model):

    '''DangerSigns store'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Danger Sign")
        verbose_name_plural = _(u"Danger Signs")

    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)
