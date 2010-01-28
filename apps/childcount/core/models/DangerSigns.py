#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

DangerSigns - DangerSigns store
'''

from django.db import models


class DangerSigns(models.Model):
    '''DangerSigns store'''

    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)
