#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import django_tables as tables

class HealthUnitsTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    code = tables.Column(verbose_name="Code")
    name = tables.Column(verbose_name="Name")
    hctype = tables.Column(verbose_name="Type")
    hsd = tables.Column(verbose_name="HSD")
    last = tables.Column(verbose_name="Last Report", sortable=False)
    last_pk = tables.Column(visible=False, sortable=False)
    last_sort = tables.Column(visible=False)
    last_color = tables.Column(sortable=False, visible=False)

class HWReportersTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    alias = tables.Column(verbose_name="Alias")
    name = tables.Column(verbose_name="Name")
    hu = tables.Column(verbose_name="Health Unit")
    contact = tables.Column(verbose_name="Contact", sortable=False)
