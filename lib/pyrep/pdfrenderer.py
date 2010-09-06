# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

""" 
PDF renderer 
Renders a report to a PDF file using the ReportLab library (www.reportlab.org)
"""

import os
import tempfile
import sys

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm as rl_mm

from font import Font

from base import *

class PDFRenderer(Renderer):
    """
    Renderer class.
    """
        
    def render(self, *args, **kwargs):
        """
        Make a PDF file 
        @keyword outfile: Output file name, if not given a temporary file will be created
        @keyword show: If True, the generated PDF file will be shown with the  default system PDF reader
        @keyword show_with: The complete path of the program to use to show the PDF 
        @return: The path of the new PDF file
        """
        super(PDFRenderer, self).render(*args, **kwargs)
        
        # Open out file
        if 'outfile' in kwargs:
            outfile = kwargs['outfile']
        else:
            out = tempfile.mkstemp(".pdf","REP_")
            os.close(out[0])
            outfile = out[1]
            
        c=canvas.Canvas(outfile)

        # Set Page Size
        c.setPageSize((rl_mm*self.report.page.width,rl_mm*self.report.page.height,))
        
        self._canvas=c

        self.report.process(self)
        
        c.save()
        
        if kwargs.get("show", False):
            show_with = kwargs.get("show_with", "")
            if not show_with:
                if sys.platform == "darwin":
                    os.system("open %s"%outfile)
                elif sys.platform == "win32":
                    os.startfile(outfile)
                else:
                    raise ReportError("Please pass the show_with parameter - No default PDF viewer!")
                
            else:
                os.system("%s %s"%(show_with, outfile))
        
        return outfile
    
    def finalize_page(self):
        """
        Called on page end
        """
        super(PDFRenderer, self).finalize_page()

        self._canvas.showPage()
        
    def _translate_coords(self, obj, x = None, y = None):
        """
        Translates coordinates from PyRep's convention (left to right and top to bottom) to ReportLab's
        """
        
        if x is None:
            x = obj.x
        
        if y is None:
            y = obj.y
            
        x += obj.parent.x
        y = self.report.page.height - obj.parent.y - y
        
        if hasattr(obj, "font"):
            y -= obj.font.size / rl_mm

        return tuple(n*rl_mm for n in (x,y))
    
    def _translate_color(self, *colors):
        """
        ReportLab accepts RGB color values as a number between 0.0 and 1.0. We prefer to use the 
        usual 0-255 range, so we have to translate it.
        The parameter may be in various formats:
        If just a number, we return it translated
        If a list of numbers, we return a tuple of translated values
        If a Color object, we return a tuple of translated (r, g, b).
        @param colors: The color(s) to translate
        """
        
        if len(colors) == 1:
            if isinstance(colors[0], Color):
                return tuple( (1.0 / 255 * x for x in colors[0]))
                
        ret = tuple( (1.0 / 255 * x for x in colors) )
        
        if len(ret) == 1:
            return ret[0]

        return ret
        
    def _set_font(self, font):
        """
        Sets the current font
        """

        for face in font.faces:
            try:
                if Font.BOLD and Font.ITALIC in font.style:
                    face+="-BoldOblique"
                elif Font.BOLD in font.style:
                    face+="-Bold"
                elif Font.ITALIC in font.style:
                    face+="-Oblique"
                    
                self._canvas.setFont(face,font.size)
            except KeyError:
                continue
            else:
                font.face=face
                break
        else:
            raise ReportError("No available fonts. Font list: %s"%font.faces)

    def draw_text(self, text, environment = None):
        """
        Draws a text object
        """
        
        x, y = self._translate_coords(text)
        
        txt = str(self.safe_eval(text.value, environment))
        
        self._canvas.saveState()
        
        self._set_font(text.font)
        
        fc = text.color
        if fc is None:
            fc = text.parent.color
        
        self._canvas.setFillColorRGB(*self._translate_color(fc))

        # TODO: Find a better way to do it
        if text.width:
            length = self._canvas.stringWidth(txt, text.font.face, text.font.size)
            while length > text.width * rl_mm:
                txt = txt[:-1]
                length = self._canvas.stringWidth(txt, text.font.face, text.font.size)

        if text.alignment == Text.ALIGN_LEFT:
            self._canvas.drawString(x,y,txt)
        elif text.alignment == Text.ALIGN_CENTER:
            self._canvas.drawCentredString(x + (text.width * rl_mm * 0.5), y, txt)
        elif text.alignment == Text.ALIGN_RIGHT:
            self._canvas.drawRightString( x + text.width * rl_mm, y, txt)
        
        self._canvas.restoreState()
        
    def draw_hline(self, shape, environment = None):
        """
        Draws an horizontal line
        """
        
        x, y = self._translate_coords(shape)
        x2, y2 = self._translate_coords(shape, (x + shape.width), y)

        self._canvas.saveState()

        if shape.color is None:
            fc = shape.parent.color
        else:
            fc = shape.color
            
        self._canvas.setStrokeColorRGB(*self._translate_color(fc))

        self._canvas.setLineWidth(shape.linewidth * rl_mm)
        
        self._canvas.line(x, y, x2, y)

        self._canvas.restoreState()

    def draw_vline(self, shape, environment = None):
        """
        Draws a vertical line
        """

        x, y = self._translate_coords(shape)
        x2, y2 = self._translate_coords(shape, shape.x, (shape.y + shape.height) )

        self._canvas.saveState()

        if shape.color is None:
            fc = shape.parent.color
        else:
            fc = shape.color
            
        self._canvas.setStrokeColorRGB(*self._translate_color(fc))
        
        self._canvas.setLineWidth(shape.linewidth * rl_mm)

        self._canvas.line(x, y, x, y2)
        
        self._canvas.restoreState()

    def draw_box(self, box, environment = None):
        """
        Draws a box (may have rounded corners)
        """
        
        x, y = self._translate_coords(box)
        
        self._canvas.saveState()
        
        self._canvas.setLineWidth(box.linewidth * rl_mm)
        
        if box.backcolor is None:
            bc = box.parent.backcolor
        else:
            bc = box.backcolor
        
        self._canvas.setFillColorRGB(*self._translate_color(bc))
        
        if box.color is None:
            fc = box.parent.color
        else:
            fc = box.color
            
        self._canvas.setStrokeColorRGB(*self._translate_color(fc))

        self._canvas.roundRect(x, y - box.height * rl_mm, box.width * rl_mm, box.height * rl_mm, box.round, fill = 1)
        
        self._canvas.restoreState()
