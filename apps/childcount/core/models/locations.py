#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Should contain location related models

Clinic
Zone
'''

from locations.models import Location


class Clinic(Location):
    pass


class Zone(Location):
    pass
