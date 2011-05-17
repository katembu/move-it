#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
from datetime import datetime

from django.utils.translation import gettext as _

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
from childcount.utils import RotatedParagraph

from childcount.indicators import registration
from childcount.indicators import household
from childcount.indicators import family_planning
from childcount.indicators import danger_signs
from childcount.indicators import referral
from childcount.indicators import follow_up
from childcount.indicators import pregnancy
from childcount.indicators import birth
from childcount.indicators import neonatal
from childcount.indicators import under_one
from childcount.indicators import nutrition
from childcount.indicators import fever
from childcount.indicators import medicine_given

from libreport.pdfreport import p

from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class ReportDefinition(PrintedReport):
    title = 'Operational Report'
    filename = 'operational_report'
    formats = ('pdf',)

    _indicators = (
        {
            'title': _("Household"),
            'columns': [
                {'name': _("Households"), 'ind': registration.Household},
                {'name': _("Total HH Visits"), 'ind': household.Total},
                {'name': _("% HH Coverage"), 'ind': household.CoveragePerc}
            ]
        },
        {
            'title': _("Family Planning"),
            'columns': [
                {'name': _("Women 15-49 Seen"), 'ind': family_planning.Women},
                {'name': _("Women Using FP"), 'ind': family_planning.Using},
                {'name': _("Women Starting FP (or Never Registered)"),
                    'ind': family_planning.Starting},
            ]
        },
        {
            'title': _("Follow Up"),
            'columns': [
                {'name': _("People with DSs"), 'ind': danger_signs.Total},
                {'name': _("Urgent (Non-Convenient) Referrals"),
                    'ind': referral.Urgent},
                {'name': _("On-Time Follow-Up Visits (between 18 and 72 hours)"), \
                    'ind': follow_up.OnTime},
                {'name': _("Late Follow-Up Visits (between 72 hours and 7 days)"), \
                    'ind': follow_up.Late},
                {'name': _("No Follow-Up Visits (never or after 7 days)"), \
                    'ind': follow_up.Never},
            ]
        },
        {
            'title': _("Pregnancy"),
            'columns': [
                {'name': _("Pregnant Women"), 'ind': pregnancy.Total},
                {'name': _("Births"), 'ind': birth.Total},
                {'name': _("Births with 4 ANC"), 'ind': birth.WithAncFour},
                {'name': _("Babies Known Delivered in Clinic"), \
                    'ind': birth.DeliveredInClinic},
                {'name': _("Neonatal Reports (within 7 days)"), \
                    'ind': neonatal.WithinSevenDaysOfBirth},
            ]
        },
        {
            'title': _("Under Five"),
            'columns': [
                {'name': _("Children U5"), 'ind': registration.UnderFive},
                {'name': _("Children U5 Known Immunized"),\
                    'ind': under_one.UnderFiveImmunizationUpToDate},
                {'name': _("MUACs Taken"), 'ind': nutrition.Total},
                {'name': _("Active SAM/MAM Cases"), 'ind': nutrition.SamOrMam},
            ]
        },
        {
            'title': _("Malaria"),
            'columns': [
                {'name': _("Tested RDTs"), 'ind': fever.Total},
                {'name': _("Positive RDTs"), 'ind': fever.RdtPositive},
                {'name': _("Anti-malarials Given"), 'ind': medicine_given.Antimalarial},
            ]
        },
        {
            'title': _("Diarrhea"),
            'columns': [
                {'name': _("U5 Diarrhea Cases"), 'ind': danger_signs.UnderFiveDiarrhea},
                {'name': _("ORS Given"), 'ind': medicine_given.Ors},
            ]
        },
    )

    def generate(self, period, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')

        self.set_progress(0.0)

        story = []
        locations = Clinic\
            .objects\
            .filter(pk__in=CHW.objects.values('clinic').distinct())

        total = locations.count()
        for i,location in enumerate(locations):
            self.set_progress(100.0*i/total)

            rowCHWs = CHW\
                        .objects\
                        .filter(is_active=True)\
                        .filter(clinic=location)
            if rowCHWs.count() == 0:
                continue

            tb = self._operationalreportable(period, location, rowCHWs)

            story.append(tb)
            story.append(PageBreak())

        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        f.close()

    def _operationalreportable(self, period, title, chws):
        tStyle = [('INNERGRID', (0, 0), (-1, -1), 0.1, colors.lightgrey),\
                ('BOX', (0, 0), (-1, -1), 0.1, colors.lightgrey)]
        rowHeights = []
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleH3.fontSize = 10
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT
        styleBold = copy.copy(styleN)
        styleBold.fontName = 'Times-Bold'

        ''' Header data '''
        now = datetime.now()
        hdata = [Paragraph(_(u'%(name)s - %(title)s '\
                                '(Generated on '\
                                '%(gen_date)s at %(gen_time)s)') % \
                                {'name': title,\
                                'title': period.title,\
                                'gen_date': now.strftime('%d %b %Y'),\
                                'gen_time': now.strftime('%H:%M')}, \
                styleH3)]
        tStyle.append(('SPAN', (0, 0), (-1, 0)))

        ncols = sum([len(c['columns']) for c in self._indicators])
        hdata.extend((ncols - 1) * [''])
        rowHeights.append(None)
        data = [hdata]

        group_row = ['']
        thirdrow = [Paragraph('CHW Name', styleH3)]

        # Row index
        index = 1

        # Col index
        i = 0

        colWidths = [1.4 * inch]
        for g in self._indicators:
            group_len = len(g['columns'])
            
            # Title string
            group_row.append(Paragraph(g['title'], styleH3))
            group_row.extend([''] * (group_len - 1))

            # Add a box around odd-indexed column groups
            if i % 2 == 1:
                tStyle.append(('BOX', (index, 1), (index + group_len - 1, -1), \
                                        2, colors.lightgrey))
            tStyle.append(('SPAN', (index, 1), (index + group_len - 1, 1)))
            index += group_len
            i += 1

            # Column headers
            for col in g['columns']:
                p = RotatedParagraph(Paragraph((col['name']), styleN), \
                    2.3*inch, 0.25*inch)
                thirdrow.append(p)

                # Give percentages wide columns
                colWidths.append((0.4 * inch))

        data.append(group_row)
        rowHeights.append(None)

        data.append(thirdrow)
        rowHeights.append(2.3*inch)
    
        def format_val(ind, val):
            if ind.output_is_percentage():
                return val.short_str()
            else:
                return unicode(val)

        if len(chws) > 0:
            rows = []
            for chw in chws:
                row = [Paragraph(chw.full_name(), styleN)]
                for group in self._indicators:
                    for pair in group['columns']:
                        print pair['name']
                        value = pair['ind'](period, chw.patient_set.all())
                        row.append(Paragraph(format_val(pair['ind'], value), styleN))

                rows.append(row)
         
            # Get totals for the clinic
            patients = Patient.objects.filter(chw__clinic__pk=chws[0].clinic.pk)
            row = [Paragraph(chw.clinic.name, styleBold)]
            for group in self._indicators:
                for pair in group['columns']:
                    print pair['name']
                    value = pair['ind'](period, patients)
                    row.append(Paragraph(format_val(pair['ind'], value), styleN))
            rows.append(row)

            rowHeights.extend(len(rows) * [0.25 * inch])

            # Add data to table
            data.extend(rows)
            tStyle.append(('LINEABOVE', (0, 3), (-1, 3), 0.5, colors.black))
            tStyle.append(('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black))

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle(tStyle)) 
        
        return tb
