#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''
Should contain abstract classes of reusable fields.  These models do not
have a table in the database. They are shared because they are used by
multiple report models. A report model simply needs to extend one of the
classes below, and that field will then be included in that model.

Fields:
    GenderField
    RDTField
    DangerSignsField

'''

from django.db import models
from django.utils.translation import ugettext as _


class GenderField(models.Model):

    '''A single field to represent gender in models'''

    class Meta:
        app_label = 'childcount'
        abstract = True

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)


class RDTField(models.Model):

    '''A single field to represent an RDT test result'''

    class Meta:
        app_label = 'childcount'
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

    '''
    A single field to indicate whether danger signs are present.
    Note: This is not where the danger signs themselves are stored, this is
    simply a single character indicating whether there ARE danger signs.
    '''

    class Meta:
        app_label = 'childcount'
        abstract = True

    DANGER_SIGNS_PRESENT = 'S'
    DANGER_SIGNS_NONE = 'N'
    DANGER_SIGNS_UNKOWN = 'U'
    DANGER_SIGNS_UNAVAILABLE = 'W'

    DANGER_SIGNS_CHOICES = (
        (DANGER_SIGNS_PRESENT, _(u"Present")),
        (DANGER_SIGNS_NONE, _(u"None")),
        (DANGER_SIGNS_UNKOWN, _(u"Unknown")),
        (DANGER_SIGNS_UNAVAILABLE, _(u"Unavailable")))

    danger_signs = models.CharField(_(u"Danger Signs"), max_length=1, \
                                    choices=DANGER_SIGNS_CHOICES)
