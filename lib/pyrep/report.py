# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

""" 
Report class

"""

from base import *

class Report(object):
    """
    The Report class. It represents the whole report.
    A Report sits on its page (a Page object) and it's divided into several Sections (or bands):
    1. Title - Printed only once per report, is the report's title
    2. Header - Printed once per page, is the page's header
    3. Body - Printed once per datasource's row, is the actual report body
    4. Footer - Printed once per page, at the page's end
    5. Summary - Printed once per report, after report's end. This is a good place to put totalizations, calculations, and so on.
    More features of the Report object:
    - A report can have several groups. Look at Group's doc for details
    - A report can have one or more subreports. NOT YET IMPLEMENTED
    - You can define report-based variables, that may contain calculations, or any valid python expression computed at runtime
    - You can define parameters, that are variables you pass to the report
    - Each report can have several data sources to get data from, although the main datasource is only one per report (or subreport)
    
    @ivar page: The Page object on which the reports is printed
    @ivar preferred_renderer: The preferred renderer for this report. Optional
    @ivar title: The Title band
    @ivar header: The Header band
    @ivar body: The Body band
    @ivar footer: The Footer band
    @ivar summary: The Summary band
    @ivar groups: The group list
    @ivar subreports: Subreports list
    @ivar variables: List of report-defined variables
    @ivar parameters: List of report-defined parameters
    @ivar calculations: Aggregate calculation run by the engine using any available data (datasources, variables, parameters and so on). 
    @ivar datasources: List of report's datasources
    @ivar fonts: Report fonts
    """
    
    def __init__(self, page = Page('A4')):
        
        self.page = page
        
        # Preferred renderer
        self.preferred_renderer = None
        
        # Title band (printed only once per report)
        self.title = Section(self, (None, 0))
        
        # Page header (printed once per page)
        self.header = Section(self, (None, 0))
        
        # Report detail (body)
        self.body = Section(self, (None, 0))
        
        # Page footer (once per page)
        self.footer = Section(self, (None, 0))
        
        # Report summary (printed after report's end)
        self.summary = Section(self, (None, 0))
        
        # Groups of data
        self.groups = list()
        
        # Subreports
        self.subreports = list()
        
        # Variables
        self.variables = dict()
        
        # Parameters
        self.parameters = dict()
        
        # Calculations
        self.calculations = list()
        
        # Report-defined data sources
        self.datasources = dict()
        
        # Fonts
        self.fonts = dict()
    
    def check_sections_height(self):
        """
        Checks if header + body + footer height exceed page's size. 
        @raises ReportError: if it exceeds
        """
        
        heights = list()
        
        for s in ("title", "header", "body", "footer"):
            try:
                h = getattr(self, s).height
                heights.append(h)
            except AttributeError:
                heights.append(0.0)
        
        total_height = sum(heights)
        
        if total_height > self.page.height:
            raise ReportError("Not enough space for body (page: %s, sections: %s)!"%(self.page.height, total_height))
            
    def add_variable(self, var):
        """
        Adds a new variable to this report
        @param var: Variable object
        @type var: Variable
        """
        self.variables[var.name] = var
    
    def add_parameter(self, par):
        """
        Adds a new parameter to this report
        @param par: Parameter object
        @type par: Parameter
        """
        self.parameters[par.name] = par
    
    def add_calculation(self, calc):
        """
        Adds a new aggregate calculation to this report
        @param calc: Calculation object
        @type calc: Calculation
        """
        calc.report = self
        self.calculations.append(calc)
    
    def register_font(self, font):
        """
        Registers a new font for this report
        @param font: The font object
        @type font: Font
        """
        self.fonts[font.id] = font
        
    def get_font(self, name):
        """
        Gets the font named "name" in this report, if exists
        @param name: The font's name (as registered)
        @type name: string
        @raise ReportError: When there is no registered font with name "name"
        """
        try:
            return self.fonts[name]
        except KeyError:
            raise ReportError("Unregistered font name: %s"%name)
    
    def get_size(self):
        """
        Returns the current report page's size
        """
        return self.page.size
    
    size = property(get_size, None, None, """ Report's size is page's size! """)

    def _draw_new_page(self, renderer, environment):
        renderer.start_page()
        
        # If this is the first page, draw the title band (only once per report)
        if self.pagenum == 0:
            y = self.title.y
            self.title.draw(renderer, environment)
            y += self.title.height
        else:
            y = 0

        self.header.y = y
        
        self.pagenum += 1
        self.header.draw(renderer, environment)
        y += self.header.height

        self.body.y = y
        
        return y

    def _draw_footer(self, renderer, environment):
        self.footer.y = self.page.height - self.footer.height
        self.footer.draw(renderer, environment)
        renderer.finalize_page()

    def process(self, renderer):
        """
        Starts processing the report.
        @param renderer: The Renderer object to draw to
        """

        self.check_sections_height()

        self.pagenum = 0
        reset_calcs = False
        self.currentrow = None
        
        environment = Data(self)

        # Flag to know if we should create a new page
        newpage = True

        # Current record number
        rec_number = 0

        # Flag to block iterator advance
        block_iter = False
        
        # Flag to indicate that we have already drawn the footer (needed to avoid drawing 
        # the footer twice when the last record consumes exactly all the space)
        footer_drawn = False
        
        # Cycle through the datasource
        datasource = iter(renderer.maindatasource)
        
        while(True):
            if not block_iter:
                try:
                    self.currentrow = datasource.next()
                    rec_number += 1
                except StopIteration:
                    break

            if newpage:
                y = self._draw_new_page(renderer, environment)
                
                block_iter = False
                newpage = False
                footer_drawn = False

            # If y position exceeds body's reserved space, draws the footer
            # and starts a new page
            if (y + self.body.height) > self.page.height - self.footer.height:
                # Draws footer
                self._draw_footer(renderer, environment)
                
                newpage = True
                block_iter = True
                footer_drawn = True
                
                continue

            # Execute report's calculations
            for calc in self.calculations:
                calc.execute(renderer, environment)
                
            # Draws body band
            self.body.draw(renderer, environment)
            y += self.body.height
            self.body.y = y

            if reset_calcs:
                reset_calcs = False
                # Reset page-resetted calcs
                for calc in self.calculations:
                    if calc.reset_at == "page":
                        calc.reset()

        if not rec_number:
            raise ReportError("No data available!")

        # Draws summary band
        if self.summary.height < self.page.height - self.footer.height - y:
            self.summary.y = y
            self.summary.draw(renderer, environment)
            if not footer_drawn:
                self._draw_footer(renderer, environment)
        else:
            if not footer_drawn:
                self._draw_footer(renderer, environment)
            # New page
            y = self._draw_new_page(renderer, environment)
            self.summary.y = y
            self.summary.draw(renderer, environment)
            self._draw_footer(renderer, environment)
