#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import copy

from django import template

from reportlab.lib.units import cm 
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, Paragraph, Frame, BaseDocTemplate
from reportlab.platypus import PageTemplate, Spacer

from ccdoc.generator import Generator


class PDFGenerator(Generator):
    def _start_document(self):
        self.PAGE_HEIGHT = 21.0 * cm
        self.PAGE_WIDTH = 29.7 * cm

        self.text_templ = template.Template('{{text}}')

        self.styles = getSampleStyleSheet()

        self.styles['Normal'].fontName = 'Helvetica'
        self.styles['Normal'].fontSize = 10

        ''' All Flowable elements on the page '''
        self.elements = []

        ''' Overall document object describing PDF '''
        self.doc = BaseDocTemplate(self._handle,
            showBoundary=0,
            title = unicode(self.title))

        ''' Frame template defining page size, margins, etc '''
        self.tframe = Frame(1.5 * cm, 1.5 * cm,
                        self.PAGE_HEIGHT - 3 * cm,  self.PAGE_WIDTH - 3 * cm,
                       showBoundary=0, topPadding=0, bottomPadding=0,
                       rightPadding=0, leftPadding=0)

        self.section_style = copy.copy(self.styles['Normal'])
        self.section_style.fontSize = 18
        self.section_style.leading = 20
        self.section_style.spaceBefore = 1 * cm

        ''' Table style '''
        self.table_style = copy.copy(self.styles['Normal'])
        self.table_style.fontSize = 9
        self.table_style.leading = 10
        self.table_style.alignment = 1

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

        c = template.Context({'text': unicode(text.text)})
        ''' 
            Render using Django templates to avoid
            issues with special characters, escapes, etc, etc
        '''
        output = self.text_templ.render(c)

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
            tabstyle.append(('GRID', (0,1), (-1,-1), 0.25, colors.black))
            tabstyle.append(('BOTTOMPADDING', (0,0), (0, 0), 6))
        

        ''' Iterate through each table row '''
        i = 1; j=1
        for row in table.rows:
            rowdata = []

            # row[0] is true when this is a header row
            for c in row[1]:
                if row[0]:
                    j = 1; c.bold = True
                    tabstyle.append(('LINEBELOW', (0, i), (-1, i), 0.25, colors.black))
                rowdata.append(Paragraph(self._render_text(c), self.table_style))
            tabdata.append(rowdata)

            # Zebra stripes (not on header rows)
            if j % 2 == 0 and not row[0]:
                tabstyle.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eeeeee')))

            i += 1; j += 1

        ''' Align all in middle '''
        tabstyle.append(('LEFTPADDING', (0,0), (-1,-1), 1))
        tabstyle.append(('RIGHTPADDING', (0,0), (-1,-1), 1))
        tabstyle.append(('TOPPADDING', (0,0), (-1,-1), 1))
        tabstyle.append(('BOTTOMPADDING', (0,0), (-1,-1), 2))

        table = Table(tabdata, style=tabstyle)
        self.elements.append(table)

    def _end_document(self):
        template = PageTemplate('normal', [self.tframe])
        self.doc.addPageTemplates(template)
        self.doc.build(self.elements)


