#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''core logic'''

import re
import time
from datetime import datetime, timedelta, date

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.models import Patient
from childcount.models.reports import HouseHoldVisitReport
from childcount.models.reports import PregnancyReport
from childcount.models.reports import DeathReport
from childcount.models import Case, Referral
from childcount.models.reports import BirthReport, HealthReport


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass












