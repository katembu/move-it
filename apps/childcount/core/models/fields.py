#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Should contain abstract classes of reusable fields'''

from django.db import models
from django.utils.translation import ugettext_lazy as _


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


class RDTField(models.Model):
    '''
    This is an abstract class that includes an RDT field.  It does not
    have a table in the database, and is only used by extending it by other
    model classes. Any class that extends it will have an rdt_result field.
    '''
    class Meta:
        abstract = True

    RDT_POSITIVE = 'P'
    RDT_NEGATIVE = 'N'
    RDT_UNKOWN = 'U'
    RDT_UNAVAILABLE = 'X'

    RDT_CHOICES = (
        (RDT_POSITIVE, _(u"Positive")),
        (RDT_NEGATIVE, _(u"Negative")),
        (RDT_UNKOWN, _(u"Unknown")),
        (RDT_UNAVAILABLE, _(u"Test unavailable")))

    rdt_result = models.CharField(_(u"RDT Result"), max_length=1, \
                                  choices=RDT_CHOICES)


class DangerSignsField(models.Model):
    class Meta:
        abstract = True

    DANGER_SIGNS_PRESENT = 'S'
    DANGER_SIGNS_NONE = 'N'
    DANGER_SIGNS_UNKOWN = 'U'

    DANGER_SIGNS_CHOICES = (
        (DANGER_SIGNS_PRESENT, _(u"Present")),
        (DANGER_SIGNS_NONE, _(u"None")),
        (DANGER_SIGNS_UNKOWN, _(u"Unknown")))

    danger_signs = models.CharField(_(u"Danger Signs"), max_length=1, \
                                    choices=DANGER_SIGNS_CHOICES)
