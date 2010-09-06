# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

"""
    Module to parse a report definition file
"""

import logging

import xml.dom.minidom

import dataproviders

from base import *
from report import Report

class XMLParser(object):
    """
        Parses an XML report definition file.
        Look at the report.dtd for XML schema
    """
    
    def __init__(self, **kwargs):
        """
        Constructor. "filename" parameter take precedence over "xmlcontent"
         
        @param filename: File's name
        @param xmlcontent: XML code
        """
        
        self._filename = kwargs.get("filename", None)
        self._xmlcontent = kwargs.get("xmlcontent", None)
        
        if self._filename is None and self._xmlcontent is None:
            raise ReportError("Please pass a file name or an xml content to parse!")
    
    def parse(self):
        """
        Parses the file
        @returns: a Report object
        """
        
        try:
            if self._filename:
                # Open XML file 
                try:
                    f = open(self._filename, "rb")
                except IOError, e:
                    raise ReportError("Unable to open report file <%s>.\n%s"%(self._filename, e))
                
                content = xml.dom.minidom.parse(f)
            else:
                content = xml.dom.minidom.parseString(self._xmlcontent)
        except Exception, e:
            raise ReportError("Parsing error:\n%s"%e)
            
        report = content.documentElement
        # Check out XML schema
        if report.nodeName != "report":
            raise ReportError("%s: Invalid report file! Root element is <%s>"%(self._filename, report.nodeName))
        
        # Builds the Report object
        self.rpt=Report()

        # Analyze report's attributes
        if report.hasAttribute("pagesize"):
            report.page = Page(report.getAttribute("pagesize"))
        if report.hasAttribute("renderer"):
            renderer = report.getAttribute("renderer")
            logging.warn("Preferred renderer not implemented yet!")

        # Start processing of top-level elements
        for element in report.childNodes:
            if element.nodeType != element.ELEMENT_NODE:
                continue
            
            name = element.nodeName
            
            if name == "font":
                self._parse_font(element)
            elif name in "title,header,body,footer,summary".split(","):
                self._process_section(element)
            elif name == "datasources":
                self._process_datasources(element)
            else:
                logging.warn("Invalid element in report definition file: %s"%name)
                
        
        return self.rpt
            
    
    def _parse_font(self, element):
        id = None
        size = None
        italic = False
        bold = False
        
        if element.hasAttribute("id"):
            id = element.getAttribute("id")
            
        if element.hasAttribute("face"):
            face = element.getAttribute("face")
        else:
            raise ReportError("Font face not specified")
        
        if element.hasAttribute("size"):
            size = int(element.getAttribute("size"))
            if size <= 0:
                raise ReportError("Invalid font size!")
        else:
            raise ReportError("Font size not specified")
        
        if element.hasAttribute("italic"):
            if element.getAttribute("italic").lower() == "true":
                italic = True
            if element.getAttribute("bold").lower() == "true":
                bold = True
            
        style = list()
        if italic:
            style.append(Font.ITALIC)
        if bold:
            style.append(Font.BOLD)
            
        f = Font(id, face, size, style)
            
        self.rpt.register_font(f)
        
    def _process_section(self, element):
        section = getattr(self.rpt, element.nodeName)
        
        section.size = self.get_size(element)
        
        if element.hasAttribute("font"):
            section.default_font = self.rpt.get_font(element.getAttribute("font"))
        
        # Process children
        for child in element.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            
            name = child.nodeName
            
            if hasattr(self,"_process_child_%s"%name):
                getattr(self,"_process_child_%s"%name)(section, child)
            else:
                logging.warn("Invalid child type: %s"%name)
                
    def _process_child_text(self, section, element):
        size = self.get_size(element)
        position = self.get_position(element)
        align = Text.ALIGN_LEFT
        
        if element.hasAttribute("alignment"):
            a = element.getAttribute("alignment")
            if a == "left":
                align = Text.ALIGN_LEFT
            elif a == "center":
                align = Text.ALIGN_CENTER
            elif a == "right":
                align = Text.ALIGN_RIGHT
            else:
                logging.warn("Invalid alignment: %s"%a)
        
        value=[]
        for child in element.childNodes:
            if child.nodeType == child.TEXT_NODE:
                value.append(child.nodeValue.strip())
        value = "\n".join(value)

        kwargs = dict( value = value, alignment = align)

        if element.hasAttribute("font"):
            kwargs["font"] = self.rpt.get_font(element.getAttribute("font"))

        if element.hasAttribute("color"):
            kwargs["color"] = Color.from_hex(element.getAttribute("color"))

        text = Text(size, **kwargs)
        
        section.add_child(position, text)
    
    def _process_child_hline(self, section, element):
        position = self.get_position(element)
        size = self.get_size(element)
        
        line = HLine(size[0])
        
        section.add_child(position, line)            

    def _process_child_box(self, section, element):
        position = self.get_position(element)
        size = self.get_size(element)

        if element.hasAttribute("linewidth"):
            linewidth = self.parse_number(element.getAttribute("linewidth"))
        else:
            linewidth = 0.2

        if element.hasAttribute("bordercolor"):
            bordercolor = Color.from_hex(element.getAttribute("bordercolor"))
        else:
            bordercolor = Color.BLACK

        if element.hasAttribute("fillcolor"):
            fillcolor = Color.from_hex(element.getAttribute("fillcolor"))
        else:
            fillcolor = Color.WHITE

        if element.hasAttribute("round"):
            round = self.parse_number(element.getAttribute("round"), False)
        else:
            round = 0
            
        box = Box(size, linewidth, Shape.SOLID, bordercolor, fillcolor, round = round)

        section.add_child(position, box)

    def _process_datasources(self, element):
        # Process children
        for datasource in element.childNodes:
            if datasource.nodeType != datasource.ELEMENT_NODE:
                continue
            
            name = datasource.nodeName
            
            if name != "datasource":
                logging.warn("Invalid child for datasources: %s"%name)
                continue
            
            dsname = datasource.getAttribute("name")
            dstype = datasource.getAttribute("type")
            dsengine = datasource.getAttribute("engine")
            
            if dstype == "dbapi2":
                dsquery=[]
                for line in datasource.childNodes:
                    if line.nodeType == line.TEXT_NODE:
                        dsquery.append(line.nodeValue.strip())
                dsquery = "\n".join(dsquery)
                    
                ds = dataproviders.DBDataProvider(dsquery)
                self.rpt.datasources[dsname] = ds
            
    def get_size(self, element):
        w, h = -1, -1
        
        if element.hasAttribute("width"):
            w = self.parse_number(element.getAttribute("width"))
            
        if element.hasAttribute("height"):
            h = self.parse_number(element.getAttribute("height"))
        
        return w, h
    
    def get_position(self, element):
        x, y = 0, 0
        
        if element.hasAttribute("x"):
            x = self.parse_number(element.getAttribute("x"))

        if element.hasAttribute("y"):
            y = self.parse_number(element.getAttribute("y"))
        
        return x, y

    def parse_number(self, value, parse_unit = True):
        """
        Parses a string value in the form numberunit or number unit
        For example: 12cm or 12 cm
        @param value: The string to parse
        @param parse_unit: If false, the number cannot contain an unit of measurement
        @returns: a numeric value in mm
        @raise: a ReportError on bad format
        """
        
        if value is None:
            return None
        if value == "all":
            return None
            
        n=""
        m=""
        nums="0123456789,.-"
        
        # Process number
        i=0
        while i < len(value):
            c=value[i]
            if not c in nums:
                break
            if c==',': c='.'
            n+=c
            i+=1
        
        # Process unit (if any)
        while i < len(value):
            m+=value[i]
            i+=1
            
        try:
            n=float(n)
        except ValueError,e:
            raise ReportError(e)
            
        m=m.strip()
        
        if m and not parse_unit:
            raise ReportError("Should be a pure number: %s"%value)
        
        if not m in units:
            raise ReportError("Invalid unit: %s"%m)
        
        return units[m](n)
