#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Should contain abstract classes of reusable fields'''

from django.db import models


class GenderField(models.Model):
    class Meta:
        abstract = True

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)    
