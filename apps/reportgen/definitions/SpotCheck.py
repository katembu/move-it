#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
from datetime import datetime

from django.utils.translation import ugettext as _

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from childcount.models import Clinic
from childcount.models import Patient
from childcount.models import CHW
import childcount.helpers

from childcount.utils import RotatedParagraph

from libreport.pdfreport import p

import bonjour.dates

from ccdoc.utils import register_fonts
from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleN.fontSize = 9

styleH3 = styles['Heading3']
styleH3.fontName = 'FreeSerif'
styleH3.fontSize = 12

styleH1 = styles['Heading1']
styleH1.fontSize = 14
styleH1.fontName = 'FreeSerif'

class ReportDefinition(PrintedReport):
    title = 'Spot Check'
    filename = 'spot_check_'
    formats = ('pdf',)

    variants = [(c.name, c.code, {'clinic_pk': c.pk}) \
                                    for c in Clinic.objects.all()]

    def generate(self, period, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF '\
                                        'for spot check report')

        self.period = period
        self.set_progress(0.0)

        story = []

        # Datestamp
        story.append(Paragraph(u"<b>%(name)s - %(title)s</b>" % \
                {'name': title,\
                'title': period.title}, styleH1))

        story.append(Paragraph(_('(Generated on %(gen_datetime)s)') % \
                {'gen_datetime': \
                    bonjour.dates.format_datetime(format='medium')}, styleN))

        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')

        clinic_pk = data['clinic_pk']
        location = Clinic\
            .objects\
            .get(pk=clinic_pk)

        chws = CHW\
                    .objects\
                    .filter(is_active=True)\
                    .filter(clinic=location)[0:1]

        for c in chws:
            tb = self._spot_check_table(period, c)
            story.append(tb)

        story.append(PageBreak())

        register_fonts()
        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        f.close()

    def _hh_encounter_summary(self, patient):
        master = childcount.helpers.patient.latest_hhv_raw(self.period, patient)
        if master is None:
            return _("[No HHV]")

        ccrpts = master.encounter.ccreport_set.all()
        hhvs = ccrpts.filter(polymorphic_ctype__name='Household Visit Report')
        fps = ccrpts.filter(polymorphic_ctype__name='Family Planning Report')

        out = u""
        if hhvs.count():
            hhv = hhvs[0]
            out += _("+V ")
            out += "Y" if hhv.available else "N"
            out += " "
            out += unicode(hhv.children) if hhv.available else ""

        if fps.count():
            fp = fps[0]
            out += _(" +K ")
            out += "%d " % fp.women
            out += "%d " % fp.women_using

        return out

    def _spot_check_columns(self):
        return [
            {
                'name': u"\u2714",
                'value': lambda p: u"\u2610",
            },
            {
                'name': _("Checked On"),
            },
            {
                'name': _("Location"),
                'value': lambda p: p.location.code.upper(),
            },
            {
                'name': _("HHID"),
                'value': lambda p: p.household.health_id.upper(),
            },
            {
                'name': _("Patient"),
                'value': lambda p: ("<b>%s</b>" % p.full_name()) \
                                    if p.is_head_of_household() else p.full_name(),
            },
            {
                'name': _("Last HH Visit"),
                'value': lambda p: childcount.helpers.patient.latest_hhv_date(self.period, p),
            },
            {
                'name': _("Visit Summary"),
                'value': self._hh_encounter_summary,
            },
            {
                'name': _("Notes"),
            },
        ]

    def _spot_check_table(self, period, chw):
        cols = self._spot_check_columns()
        ncols = len(cols)
       
        row_name = [[]]*ncols
        row_name[0] = Paragraph(chw.full_name(), styleH3)
        row_name[-1] = Paragraph(_("Prepared By: ____________________"), styleH3)

        row_labels = [c['name'] for c in cols]
       
        patients = Patient\
            .objects\
            .filter(encounter__encounter_date__range=(period.start, period.end),
                chw=chw)\
            .household(period.start, period.end)\
            .order_by('?')[0:5]

        table = [row_name, row_labels]

        for hh in patients: 
            row = [[]]*ncols
            for i,c in enumerate(cols):
                if 'value' in c:
                    row[i] = Paragraph(c['value'](hh), styleN)

            table.append(row) 
        
        return Table(table)
