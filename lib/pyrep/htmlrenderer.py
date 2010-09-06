# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

""" 
HTML renderer 
Renders a report to a HTML file
"""

import os
import tempfile
import sys

from base import *

class HTMLRenderer(Renderer):
    """
	Should render the report to a HTML 4.01 document.
	By now, it just doesn't work.
    """
    
    def render(self, *args, **kwargs):
        """
        Make an HTML file 
        @keyword outfile: Output file name, if not given a temporary file will be created
        @keyword show: If True, the generated HTML file will be shown with the  default system HTML reader
        @keyword show_with: The complete path of the program to use to show the HTML 
        @return: The path of the new HTML file
        """
        super(HTMLRenderer, self).render(*args, **kwargs)
        
        # Open out file
        if 'outfile' in kwargs:
            outfile = kwargs['outfile']
            out = os.open(outfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0600)
        else:
            out = tempfile.mkstemp(".html","REP_")
            outfile = out[1]
            out = out[0]

        header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<HTML>
    <HEAD>
        <TITLE>Report</TITLE>
        <STYLE type="text/css" media="all">
            @page {size: auto; margin: 0;}
            BODY {position: static;}
            DIV.page {page-break-after: always; position: fixed;}
            DIV.element {position: fixed;}
            DIV.box {position: fixed;}
            DIV.hline{position: fixed;}
            DIV.vline{position: fixed;}
        </STYLE>
    </HEAD>
    <BODY>
"""

        os.write(out, header)
        
        self.out = out
        self.report.process(self)

        footer = """
    </BODY>
</HTML>
"""
        
        os.write(out, footer)
        os.close(out)
        
        if kwargs.get("show", False):
            show_with = kwargs.get("show_with", "")
            if not show_with:
                if sys.platform == "darwin":
                    os.system("open %s"%outfile)
                elif sys.platform == "win32":
                    os.startfile(outfile)
                else:
                    raise ReportError("Please pass the show_with parameter - No default HTML viewer!")
                
            else:
                os.system("%s %s"%(show_with, outfile))
        
        return outfile
    
    def start_page(self):
        """
        Called on new page's begin
        """
        
        os.write(self.out, """<DIV class="page">\n\n""")
        
    def finalize_page(self):
        """
        Called on page end
        """
        super(HTMLRenderer, self).finalize_page()

        os.write(self.out, "\n\n</DIV>\n\n")

    def _translate_coords(self, obj, x = None, y = None):
        """
        Translates coordinates from PyRep's convention (left to right and top to bottom) to HTML's
        """

        if x is None:
            x = obj.x

        if y is None:
            y = obj.y

        x += obj.parent.x
        y = obj.parent.y + y

        # if hasattr(obj, "font"):
        #     y -= obj.font.size

        return (x,y)
    
    def _get_font(self, font):
        info = list()
        
        info.append("font-family: %s"%font.face)
        info.append("font-size: %spt"%font.size)
        
        return ";".join(info)
        
    def draw_text(self, text, environment = None):
        """
        Draws a text object
        """

        x, y = self._translate_coords(text)
        
        txt = str(self.safe_eval(text.value, environment))
        
        format = []
        align = ""
        if text.alignment == Text.ALIGN_CENTER:
            align = "text-align: center"
        elif text.alignment == Text.ALIGN_RIGHT:
            align = "text-align: right"
        
        format.append(align)
        
        if text.color is not None:
            fc = text.color.to_hex()
        else:
            fc = text.parent.color.to_hex()

        format.append("color: %s"%fc)
        
        format.append(self._get_font(text.font))
        
        format = ";".join(format)
        
        div = """<DIV class="element" style="top: %smm; left: %smm; width: %smm; height: %smm; %s">%s</DIV>\n"""%(y, x, text.width, text.height, format, txt)
        os.write(self.out, div)
        
    def draw_hline(self, shape, environment = None):
        """
        Draws an horizontal line
        """

        x, y = self._translate_coords(shape)
        
        div = """<DIV class="hline" style="top: %smm; left: %smm; width: %smm; height: %smm; border-width: %smm; border-style: solid; border-color: %s">&nbsp</DIV>\n"""%(
              y, x, shape.width, shape.linewidth/2, shape.linewidth, shape.color.to_hex())
        
        os.write(self.out, div)

    def draw_vline(self, shape, environment = None):
        """
        Draws a vertical line
        """

        x, y = self._translate_coords(shape)
        
        div = """<DIV class="vline" style="top: %smm; left: %smm; height: %smm; width: %smm; border-width: %smm; border-style: solid; border-color: %s">&nbsp</DIV>\n"""%(
              y, x, shape.height, shape.linewidth/2, shape.linewidth, shape.color.to_hex())
        
        os.write(self.out, div)

    def draw_box(self, box, environment = None):
        """
        Draws a box (may have rounded corners)
        """
        
        x, y = self._translate_coords(box)
        
        div = """<DIV class="box" style="top: %smm; left: %smm; width: %smm; height: %smm; border-width: %smm; border-style: solid; border-color: %s">&nbsp</DIV>\n"""%(
              y, x, box.width, box.height, box.linewidth, box.color.to_hex())
        
        os.write(self.out, div)