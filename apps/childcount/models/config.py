#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Config Model for child count

'''

from django.db import models


class Configuration(models.Model):

    '''Store Key/value childcount config options'''
    description = models.CharField(max_length=255, db_index=True, unique=True),
    key = models.CharField(max_length=255, db_index=True)
    value = models.CharField(max_length=255, db_index=True, blank=True)

    class Meta:
        app_label = "childcount"
