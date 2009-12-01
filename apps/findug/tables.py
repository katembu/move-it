#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import django_tables as tables

class HealthUnitsTable(tables.Table):
    pk          = tables.Column(visible=False, sortable=False)
    code        = tables.Column(verbose_name=u"Code")
    name        = tables.Column(verbose_name=u"Name")
    hctype      = tables.Column(verbose_name=u"Type")
    hsd         = tables.Column(verbose_name=u"HSD")
    reporters   = tables.Column(verbose_name=u"Reporters")
    last        = tables.Column(verbose_name=u"Last Report", sortable=False)
    last_pk     = tables.Column(visible=False, sortable=False)
    last_sort   = tables.Column(visible=False)
    last_color  = tables.Column(sortable=False, visible=False)

class HWReportersTable(tables.Table):
    pk      = tables.Column(visible=False, sortable=False)
    alias   = tables.Column(verbose_name=u"Alias")
    name    = tables.Column(verbose_name=u"Name")
    hu      = tables.Column(verbose_name=u"Health Unit")
    hu_pk   = tables.Column(visible=False, sortable=False)
    contact = tables.Column(verbose_name=u"Contact", sortable=False)

class DiseasesReportTable(tables.Table):
    af_cases    = tables.Column(verbose_name=u"C")
    af_deaths   = tables.Column(verbose_name=u"D")
    ab_cases    = tables.Column(verbose_name=u"C")
    ab_deaths   = tables.Column(verbose_name=u"D")
    rb_cases    = tables.Column(verbose_name=u"C")
    rb_deaths   = tables.Column(verbose_name=u"D")
    ch_cases    = tables.Column(verbose_name=u"C")
    ch_deaths   = tables.Column(verbose_name=u"D")
    dy_cases    = tables.Column(verbose_name=u"C")
    dy_deaths   = tables.Column(verbose_name=u"D")
    gw_cases    = tables.Column(verbose_name=u"C")
    gw_deaths   = tables.Column(verbose_name=u"D")
    ma_cases    = tables.Column(verbose_name=u"C")
    ma_deaths   = tables.Column(verbose_name=u"D")
    me_cases    = tables.Column(verbose_name=u"C")
    me_deaths   = tables.Column(verbose_name=u"D")
    mg_cases    = tables.Column(verbose_name=u"C")
    mg_deaths   = tables.Column(verbose_name=u"D")
    nt_cases    = tables.Column(verbose_name=u"C")
    nt_deaths   = tables.Column(verbose_name=u"D")
    pl_cases    = tables.Column(verbose_name=u"C")
    pl_deaths   = tables.Column(verbose_name=u"D")
    yf_cases    = tables.Column(verbose_name=u"C")
    yf_deaths   = tables.Column(verbose_name=u"D")
    vf_cases    = tables.Column(verbose_name=u"C")
    vf_deaths   = tables.Column(verbose_name=u"D")
    ei_cases    = tables.Column(verbose_name=u"C")
    ei_deaths   = tables.Column(verbose_name=u"D")
    complete    = tables.Column(visible=False, sortable=False)

    def first_column(self):
        #return self.base_columns.values()[0]
        return self.columns.all().next()

    @property
    def by_date(self):
        return self.base_columns.has_key('date')

class CasesReportTable(tables.Table):
    opd         = tables.Column(verbose_name=u"Total OPD attendence")
    suspected   = tables.Column(verbose_name=u"Suspected malaria cases")
    rdt_test    = tables.Column(verbose_name=u"RDT tested cases")
    rdt_positive= tables.Column(verbose_name=u"RDT postive cases")
    mic_test    = tables.Column(verbose_name=u"Microscopy tested cases")
    mic_positive= tables.Column(verbose_name=u"Microscopy positive cases")
    pos_u5      = tables.Column(verbose_name=u"Positive cases under 5 years")
    pos_o5      = tables.Column(verbose_name=u"Positive 5+ years")
    complete    = tables.Column(visible=False, sortable=False)

    @property
    def by_date(self):
        return self.base_columns.has_key('date')

class TreatmentsReportTable(tables.Table):
    rdt_negative    = tables.Column(verbose_name=u"RDT negative cases treated")
    rdt_positive    = tables.Column(verbose_name=u"RDT positive cases treated")
    four_to_three   = tables.Column(verbose_name=u"4+ months to 3 years")
    three_to_seven  = tables.Column(verbose_name=u"3+ to 7 years")
    seven_to_twelve = tables.Column(verbose_name=u"7+ to 12 years")
    twelve_and_above= tables.Column(verbose_name=u"12+ years")
    complete    = tables.Column(visible=False, sortable=False)

    @property
    def by_date(self):
        return self.base_columns.has_key('date')

class ACTReportTable(tables.Table):
    yellow_dispensed    = tables.Column(verbose_name=u"Yellow dispensed")
    yellow_balance      = tables.Column(verbose_name=u"Yellow balance")
    blue_dispensed      = tables.Column(verbose_name=u"Blue dispensed")
    blue_balance        = tables.Column(verbose_name=u"Blue balance")
    brown_dispensed     = tables.Column(verbose_name=u"Brown dispensed")
    brown_balance       = tables.Column(verbose_name=u"Brown balance")
    green_dispensed     = tables.Column(verbose_name=u"Green dispensed")
    green_balance       = tables.Column(verbose_name=u"Green balance")
    other_act_dispensed = tables.Column(verbose_name=u"Other ACT dispensed")
    other_act_balance   = tables.Column(verbose_name=u"Other ACT balance")
    complete            = tables.Column(visible=False, sortable=False)

    @property
    def by_date(self):
        return self.base_columns.has_key('date')
