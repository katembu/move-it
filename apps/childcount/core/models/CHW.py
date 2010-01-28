#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

CHW - Community Health Worker model
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from reporters.models import Reporter
from locations.models import Location


class CHW(Reporter):
    '''CHW - Community Health Worker model'''

    zones = models.ManyToManyField(Location)
    clinic = models.ForeignKey(Location)
