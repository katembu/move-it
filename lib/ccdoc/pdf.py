#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import os
import copy
import operator
from datetime import date, datetime, timedelta
from cStringIO import StringIO
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from time import localtime

from reportlab.lib.units import cm 
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, Paragraph, Frame, BaseDocTemplate
from reportlab.platypus import PageTemplate, Spacer

from ccdoc.generator import Generator


class PDFGenerator(Generator):
    def _start_document(self):
        self.HU_COL_WIDTH = 4 * cm
        self.HU_NAME_FONT_SIZE = 9
        self.HU_NAME_FONT = 'Helvetica'
        self.PAGE_HEIGHT = 21.0 * cm
        self.PAGE_WIDTH = 29.7 * cm

        self.styles = getSampleStyleSheet()

        self.styles['Normal'].fontName = 'Helvetica'
        self.styles['Normal'].fontSize = 10

        ''' All Flowable elements on the page '''
        self.elements = []

        ''' Overall document object describing PDF '''
        self.doc = BaseDocTemplate(self._handle,
            showBoundary=1,
            title = unicode(self.title))

        ''' Frame template defining page size, margins, etc '''
        self.tframe = Frame(1.5 * cm, 1.5 * cm,
                        self.PAGE_HEIGHT - 3 * cm,  self.PAGE_WIDTH - 3 * cm,
                       showBoundary=1, topPadding=0, bottomPadding=0,
                       rightPadding=0, leftPadding=0)


        self.section_style = copy.copy(self.styles['Normal'])
        self.section_style.fontSize = 18
        self.section_style.leading = 20
        self.section_style.spaceBefore = 1 * cm

        ''' Document title '''
        title_style = copy.copy(self.styles['Normal'])
        title_style.fontSize = 24
        title_style.leading = 28
        self.elements.append(Paragraph(unicode(self.title), title_style))

        ''' Subtitle '''
        if self.subtitle != None and self.subtitle != '':
            subtitle_style = copy.copy(self.styles['Normal'])
            subtitle_style.fontSize = 16
            subtitle_style.leading = 18
            subtitle_style.spaceAfter = 0.5 * cm
            self.elements.append(Paragraph(unicode(self.subtitle), subtitle_style))
       
    def _render_section(self, section):
        self.elements.append(
            Paragraph(
                u'<strong>' + unicode(section.text) + u'</strong>',
                self.section_style))

    def _render_text(self, text):
        output = u''
        if text.bold:
            output += "<strong>"
        if text.italic:
            output += "<i>"
        if text.size != text.DEFAULT_SIZE:
            output += "<font size=%d>" % text.size

        output += unicode(text.text)
        
        if text.size != text.DEFAULT_SIZE:
            ouptut += "</font>"
        if text.italic:
            output += "</i>"
        if text.bold:
            output += "</strong>"
        return output

    def _render_paragraph(self, paragraph):
        textout = u''
        for p in paragraph.contents:
            textout += self._render_text(p)

        self.elements.append(Spacer(0.5 * cm, 0.5 * cm))
        self.elements.append(Paragraph(textout, self.styles['Normal']))

    def _render_hline(self, hline):
        self.elements.append(Spacer(1 * cm, 1 * cm))

    def _render_table(self, table):
        tabdata = []
        tabstyle = []

        if table.title != None:
            title_row = [u''] * table.ncols

            title_style = copy.copy(self.styles['Normal'])
            title_style.alignment = 1 # Align center
            title_style.fontSize = 14

            title_row[0] = Paragraph(self._render_text(table.title), title_style)

            tabdata.append(title_row)
            tabstyle.append(('SPAN', (0,0), (-1, 0)))
            tabstyle.append(('ALIGN', (0,0), (0, 0), 'RIGHT'))
            tabstyle.append(('GRID', (0,1), (-1,-1), 0.25, colors.black))
            tabstyle.append(('BOTTOMPADDING', (0,0), (0, 0), 6))
        
        ''' Iterate through each table row '''
        i = 1
        for row in table.rows:
            rowdata = []
            for c in row[1]:
                if row[0]:
                    c.bold = True
                    tabstyle.append(('LINEBELOW', (0, i), (-1, i), 0.25, colors.black))
                rowdata.append(Paragraph(self._render_text(c), self.styles['Normal']))
            tabdata.append(rowdata)
            i += 1

        ''' Align all in middle '''
        #tabstyle.append(('VALIGN', (0,0), (-1,-1)))
        table = Table(tabdata, style=tabstyle)
        self.elements.append(table)

    def _end_document(self):
        '''
        # Zebra stripes
        start_row = len(header_rows) + 1
        for i in range(0, (len(clinic_rows) + len(hsd_rows)) / 2):
            ts.append(('BACKGROUND', (0, start_row + i * 2),
                      (-1, start_row + i * 2), colors.HexColor('#eaeaea')))

        # highlight the selected health unit
        highlight_row = len(header_rows) + highlight_data_row
        ts.append(('BOX', (0, highlight_row), (-1, highlight_row), 1, colors.red))

        styles = getSampleStyleSheet()
        ps = styles['Normal']
        ps.fontName = 'Helvetica'
        ps.alignment = 1

        elements = []
        p = Paragraph(u'Some junk', ps)
        elements.append(p)

        table = Table(table_data, colWidths=col_widths,
                      rowHeights=row_heights, style=ts)
        elements.append(table)

        #f.addFromList(elements, c)

        # add the health unit name title to the upper left
        #elements = []

        ps.alignment = 0
        ps.fontSize = 16
        p = Paragraph(unicode('More tezt'), ps)
        elements.append(p)
        #tframe.addFromList(elements, c)

 

        c.showPage()
        c.save()
        '''
        template = PageTemplate('normal', [self.tframe])
        self.doc.addPageTemplates(template)
        self.doc.build(self.elements)


