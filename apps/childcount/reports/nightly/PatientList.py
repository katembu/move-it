#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy

from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter, landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from libreport.pdfreport import p
from libreport.pdfreport import MultiColDocTemplate

from childcount.models import Clinic
from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import ThePatient
from childcount.reports.utils import report_filepath
from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()

styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = u'Patient List: '
    filename = 'patient_list'
    formats = ['pdf']
    variants = map(lambda c: \
        (unicode(c), c.code+'_active', {'clinic_pk': c.pk, 'active': True}),
        Clinic.objects.all())
    
    def generate(self, rformat, **kwargs):
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for patient list')

        # Make sure that user passed in a clinic 
        var_index = kwargs.get('var_index')
        if var_index is None:
            return False

        var_data = self.variants[var_index]
        clinic_pk = var_data[2]['clinic_pk']

        # Get title and filename for this version of the report
        title = self.title + var_data[0]
        filename = report_filepath(self.filename + var_data[1], rformat)
        active = var_data[2]['active']

        # Produce the report
        f = open(filename, 'w')
        clinic = Clinic.objects.get(pk=clinic_pk)
        self.gen_patient_register_pdf(f, clinic, active)
        f.close()

    def gen_patient_register_pdf(self, f, clinic, active=False):
        story = []
        chws = TheCHWReport.objects.filter(clinic=clinic)
        if not chws.count():
            story.append(Paragraph(_("No report for %s.") % clinic, styleN))
        for chw in chws:
            households = chw.households().order_by('location__code','last_name')
            if not households:
                continue
            patients = []
            boxes = []
            last_loc = None
            for household in households:
                # Put blank line between cells
                if last_loc != None and last_loc != household.location.code:
                    patients.append(ThePatient())

                trow = len(patients)
                patients.append(household)
                hs = ThePatient.objects.filter(household=household)\
                                .exclude(health_id=household.health_id)\
                                .order_by('last_name')
                if active:
                    hs = hs.filter(status=ThePatient.STATUS_ACTIVE)
                patients.extend(hs)

                last_loc = household.location.code
                brow = len(patients) - 1
                boxes.append({"top": trow, "bottom": brow})

            '''Sauri specific start: include default household id generated
            when migrating patients from old core ChildCount to the new core of
            ChildCount+'''
            if ThePatient.objects.filter(health_id='XXXXX'):
                #default_household -> dh
                dh = ThePatient.objects.get(health_id='XXXXX')
                patients.append(dh)
                hs = ThePatient.objects.filter(household=dh, \
                                                chw=chw)\
                                        .exclude(health_id=dh.health_id)
                if active:
                    hs = hs.filter(status=ThePatient.STATUS_ACTIVE)
                patients.extend(hs)
                brow = len(patients) - 1
                boxes.append({"top": trow, "bottom": brow})
            #End Sauri specific

            tb = self.thepatientregister(_(u"CHW: %(loc)s: %(chw)s") % \
                                    {'loc': clinic, 'chw': chw}, \
                                    patients, boxes)
            story.append(tb)
            story.append(PageBreak())
            # 108 is the number of rows per page, should probably put this in a
            # variable
            if (((len(patients) / 108) + 1) % 2) == 1 \
                and not (len(patients) / 108) * 108 == len(patients):
                story.append(PageBreak())
        story.insert(0, PageBreak())
        story.insert(0, PageBreak())
        story.insert(0, NextPageTemplate("laterPages"))
        doc = MultiColDocTemplate(f, 2, pagesize=A4, \
                                topMargin=(0.5 * inch), showBoundary=0)
        doc.build(story)
        return f


    def thepatientregister(self, title, indata=None, boxes=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleH5 = copy.copy(styleH3)
        styleH5.fontSize = 8
        styleN.fontSize = 8
        styleN.spaceAfter = 0
        styleN.spaceBefore = 0
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        rpt = ThePatient()
        cols = rpt.patient_register_columns()

        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        data = [hdata]

        firstrow = [Paragraph(cols[0]['name'], styleH5)]
        firstrow.extend([Paragraph(col['name'], styleH5) for col in cols[1:]])
        data.append(firstrow)

        rowHeights = [None, 0.2 * inch]
        # Loc, HID, Name
        colWidths = [0.5 * inch, 0.5 * inch, 1.3 * inch]
        colWidths.extend((len(cols) - 3) * [0.4 * inch])

        ts = [('SPAN', (0, 0), (len(cols) - 1, 0)),
                                ('LINEABOVE', (0, 1), (len(cols) - 1, 1), 1, \
                                colors.black),
                                ('LINEBELOW', (0, 1), (len(cols) - 1, 1), 1, \
                                colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey)]
        if indata:
            for row in indata:
                ctx = Context({"object": row})
                values = [Paragraph(Template(cols[0]["bit"]).render(ctx), \
                                    styleN)]
                values.extend([Paragraph(Template(cols[1]["bit"]).render(ctx), \
                                    styleN)])
                values.extend([Paragraph(Template(cols[2]["bit"]).render(ctx), \
                                    styleN)])
                values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                    styleN2) for col in cols[3:]])
                data.append(values)
            rowHeights.extend(len(indata) * [0.2 * inch])

            tscount = 0
            for box in boxes:
                if tscount % 2:
                    ts.append((('BOX', (0, box['top'] + 2), \
                            (-1, box['bottom'] + 2), 0.5, colors.black)))
                else:
                    ts.append((('BOX', (0, box['top'] + 2), \
                            (-1, box['bottom'] + 2), 0.5, colors.black)))
                ts.append((('BACKGROUND', (0, box['top'] + 2), \
                            (2, box['top'] + 2), colors.lightgrey)))
                tscount += 1
        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=2)
        tb.setStyle(TableStyle(ts))
        return tb

