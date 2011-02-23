#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from childcount.models import CHW, Clinic
from childcount.models.reports import HouseholdVisitReport
from childcount.models.reports import DangerSignsReport
from childcount.models.reports import ReferralReport
from childcount.models.reports import FamilyPlanningReport
from childcount.models.reports import NutritionReport
from childcount.models.ccreports import MonthlyCHWReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import MonthlyPeriodSet
from childcount.reports.indicator import Indicator, INDICATOR_EMPTY
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Monthly CHW Report: ")
    filename = 'monthly_chw_report_'
    formats = ['pdf','html']
    variants = map(lambda c: \
        (unicode(c), c.code, {'clinic_pk': c.pk}),
        Clinic.objects.all())


    def generate(self, rformat, title, filepath, data):
        # Make sure that user passed in a clinic 
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']

        doc = Document(title)
        doc.add_element(PageBreak())

        chws = MonthlyCHWReport\
            .objects\
            .filter(clinic__pk=clinic_pk, is_active=True)

        for chw in chws:
            doc.add_element(Section(chw.full_name())) 
            
            doc.add_element(Paragraph(_(u"For days %(start)s - %(end)s") %\
                {'start': MonthlyPeriodSet.period_start_date(0).strftime('%e %B %Y'),\
                'end': MonthlyPeriodSet.period_end_date(\
                    MonthlyPeriodSet.num_periods-1).strftime('%e %B %Y')}))

            doc.add_element(self._indicator_table(chw))
            doc.add_element(self._pregnancy_table(chw))
            doc.add_element(self._followup_table(chw))
            doc.add_element(self._muac_table(chw))
            doc.add_element(self._immunization_table(chw))

            doc.add_element(PageBreak())

        return render_doc_to_file(filepath, rformat, doc)

    def _indicator_table(self, chw):
        table = Table(6, title=Text(_(u"Indicators")))

        headers = [_(u"Indicator")]
        headers += [self._reporting_week_date_str(w) \
            for w in xrange(0, MonthlyPeriodSet.num_periods)]
        headers += [_(u"Tot/Avg")]

        table.add_header_row(map(Text, headers))

        for col in xrange(1,5):
            table.set_column_width(12, col)
        table.set_column_width(18, 5)

        for ind in chw.report_indicators():
            ind.set_excel(False)

            cols = [ind.title]
            cols += [ind.for_period(MonthlyPeriodSet, w) \
                for w in xrange(0, MonthlyPeriodSet.num_periods)]
            cols += [ind.for_total(MonthlyPeriodSet)]

            table.add_row(map(Text, cols))

        return table 

    def _followup_table(self, chw):
        table = Table(7, \
            Text(_(u"Patients Referred in the Previous 45 days "\
                "Lacking an On-Time Follow-Up Visit")))
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Household Head")),
            Text(_(u"Referral Type / Date")),
            Text(_(u"Referred For")),
            Text(_(u"Follow-Up Date")),
        ])

        for entry in chw.lacking_follow_up():
            ref = entry['referral']
            ds = entry['danger_signs']
            fu = entry['follow_up']
            patient = ref.encounter.patient
           
            urgency_str = filter(lambda x: x[0] == ref.urgency,\
                ReferralReport.URGENCY_CHOICES)[0][1]

            table.add_row([
                Text(patient.location.code),
                Text(patient.health_id.upper()),
                Text(patient.full_name() + u" / " + \
                                    patient.humanised_age()),
                Text(patient.household.full_name()),
                Text(urgency_str + _(u" on ") + \
                                     ref.encounter\
                                        .encounter_date\
                                        .strftime('%d %b %Y')),
                Text(u", ".join([sign.description \
                                    for sign in ds.danger_signs.all()]))
                    if ds else Text(_(u"[No DSs Reported]")),
                Text(_(u"Late: ") + fu\
                            .encounter\
                            .encounter_date\
                            .strftime('%d %b %Y'))\
                    if fu else Text(_(u"[No Follow-Up]"))])

        return table


    def _immunization_table(self, chw):
        table = Table(4, \
            Text(_(u"Children Under 5 Without a Known Immunization History")))
        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        for kid in chw.needing_immunizations():
            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(kid.household.full_name())])
                
        return table

    def _pregnancy_table(self, chw):
        table = Table(6, \
            Text(_(u"Women in 2nd and 3rd Trimester who haven't had ANC in 5 Weeks")))
        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last ANC")),
            Text(_(u"Approx Due Date")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.set_column_width(12, 3)
        table.set_column_width(12, 4)

        for pair in chw.pregnant_needing_anc():
            (woman, last_anc, due_date) = pair
            table.add_row([
                Text(woman.location.code),
                Text(woman.health_id.upper()),
                Text(woman.full_name() + u" / " + woman.humanised_age()),
                Text('No ANC' if last_anc is None else \
                    last_anc.strftime('%d-%b-%Y')),
                Text(due_date.strftime('%d-%b-%Y')),
                Text(woman.household.full_name())])
        return table                

    def _muac_table(self, chw):
        table = Table(7, \
            Text(_(
            u"Children without MUAC in past 1 month (SAM) " \
            "or 3 months (healthy)")))

        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last MUAC")),
            Text(_(u"MUAC Status")),
            Text(_(u"Od.")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.set_column_width(15, 3)
        table.set_column_width(15, 4)
        table.set_column_width(5, 5)
        for row in chw.kids_needing_muac():
            (kid, nut) = row

            muac_str = status_str = _(u'[No MUAC]')
            oedema_str = _(u'U')
            if nut is not None:
                muac_str = nut.encounter.encounter_date.strftime("%d-%b-%Y")
                status_str = _(u'%(status)s [%(muac)d]') % \
                    {'status': filter(lambda c: c[0] == nut.status, \
                                NutritionReport.STATUS_CHOICES)[0][1],
                    'muac': nut.muac}
                oedema_str = nut.oedema 
                            

            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(muac_str),
                Text(status_str),
                Text(oedema_str),
                Text(kid.household.full_name())
            ])

        return table

    def _reporting_week_date_str(self, week_num):
        return _(u"Week of ") + \
            MonthlyPeriodSet\
                .period_start_date(week_num)\
                .strftime('%e %b')
