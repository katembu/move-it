#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import datetime, timedelta

from rapidsms.webui.utils import render_to_response

from models import *
from utils import *
from apps.locations.models import *

from apps.libreport.pdfreport import PDFReport
from apps.libreport.csvreport import CSVReport

# Imports for epidemiological_report_pdf
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from subprocess import Popen, PIPE
from cStringIO import StringIO
from reportlab.lib.units import cm


def index(req):
    ''' Display Dashboard

    List Alert and conflicts'''

    types    = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=types)
    all = []
    for location in locations:
        loc = {}
        loc['obj']      = location
        loc['reporters']= Reporter.objects.filter(location=location)
        loc['reports']  = list(EpidemiologicalReport.objects.filter(clinic=location))
        all.append(loc)

    return render_to_response(req, 'findug/index.html', {'locations': all})

def locations_view(req):
    ''' List all locations with links to individual pages '''

    clinics  = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=clinics)
    today    = datetime.today()
    all = []
    for location in locations:
        loc = {}
        loc['obj']      = location
        loc['alias']    = location.code.upper()
        all.append(loc)

    # sort by date, descending
    all.sort(lambda x, y: cmp(x['obj'].name, y['obj'].name))
    return render_to_response(req, 'findug/locations.html', { "locations": all})

def location_view(req, location_id):
    ''' Displays a summary of location activities and history '''

    location    = Location.objects.get(id=location_id)

    return render_to_response(req, 'findug/location.html', { "location": location})

def reporters_view(req):
    ''' Displays a list of reporters '''

    def nb_alerts_for(reporter):
        
        return 0

    reporters= Reporter.objects.filter()
    all = []
    for reporter in reporters:
        rep = {}
        rep['obj']      = reporter
        rep['nb_alerts']= nb_alerts_for(reporter)
        rep['up2date']  = rep['nb_alerts'] == 0
        all.append(rep)

    # sort by date, descending
    all.sort(lambda x, y: cmp(x['obj'].alias, y['obj'].alias))
    return render_to_response(req, 'findug/reporters.html', { "reporters": all})

def reporter_view(req, reporter_id):
    ''' Displays a summary of his activities and history '''

    reporter    = Reporter.objects.get(id=reporter_id)

    return render_to_response(req, 'findug/reporter.html', { "reporter": reporter})

def report(req):

    clinics  = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=clinics)
    fields   = []
    fields.append({"name": 'PID#', "column": None, "bit": "{{ object.id }}" })
    fields.append({"name": 'NAME', "column": None, "bit": "{{ object }} {{ object.type }}" })
    
    pdfreport = PDFReport()
    pdfreport.setLandscape(False)
    pdfreport.setTitle("FIND Clinics")
    pdfreport.setTableData(locations, fields, "Table Title")
    pdfreport.setFilename("clinics")

    csvreport = CSVReport()
    csvreport.setLandscape(False)
    csvreport.setTitle("FIND Clinics")
    csvreport.setTableData(locations, fields, "Table Title")
    csvreport.setFilename("clinics")
    

    return csvreport.render()

def epidemiological_report_pdf(req, report_id):
    ''' Generates filled-in pdf copy of a completed EpidemiologicalReport object '''

    # Static source pdf to be overlayed
    PDF_SOURCE = 'apps/findug/static/epi_form_20091027.pdf'

    DATE_FORMAT = '%d/%m/%Y'

    DEFAULT_FONT_SIZE = 11
    FONT = 'Courier-Bold'

    epi_report = EpidemiologicalReport.objects.get(id=report_id)

    # temporary file-like object in which to build the pdf containing only the data numbers
    buffer = StringIO()

    # setup the empty canvas
    c = canvas.Canvas(buffer)
    c.setFont(FONT, DEFAULT_FONT_SIZE)
    
    # REPORT HEADER AND FOOTER
    def report_header_footer():

        # The y coordinates for each line of fields on the form
        first_row_y     = 26.15*cm    
        second_row_y    = 25.25*cm
        third_row_y     = 24.35*cm
        footer_row_y    =  2.10*cm

        # find the health center's subcounty parent location object
        sub_county = filter(lambda hc: hc.type.name == 'Sub County', epi_report.clinic.ancestors())[0]

        # find the health center's district parent location object
        district = filter(lambda hc: hc.type.name == 'District', epi_report.clinic.ancestors())[0]

        # create a list containing unique reporters that submitted the subreports
        reporters = set([
            epi_report.diseases.reporter,
            epi_report.malaria_cases.reporter, 
            epi_report.malaria_treatments.reporter, 
            epi_report.act_consumption.reporter,
        ])

        # initialize an empty string for the 'By' field in the form.  There can be multiple submitters
        reporters_string = ""
        # if there is only one reporter we have space for the full name
        if len(reporters) == 1: 
            reporters_string = reporters.pop().full_name().title()

        # if there are more than one reporters lets only use first name + last initial and pray that the fit
        elif len(reporters) > 1:
            for reporter in reporters:
                reporters_string += reporter.first_name.title()
                if reporter.last_name: reporters_string += reporter.last_name[0].upper()
                reporters_string += ', '
            # remove trailing comma and space
            reporters_string = reporters_string[:-2]
                    

        # A list containing dictionaries of each field in the header and footer
        # Each item in the list is a dictionary with the x and y coords and the value of the data
        data = [
            {"x":3.5*cm, "y":first_row_y, "value":datetime.today().strftime(DATE_FORMAT)}, # Date
            {"x":10.6*cm, "y":first_row_y, "value":epi_report.period.start_date.strftime(DATE_FORMAT)}, # For Period (Date)
            {"x":16.0*cm, "y":first_row_y, "value":epi_report.period.end_date.strftime(DATE_FORMAT)}, # To (Date)

            {"x":4.5*cm, "y":second_row_y, "value":'%s %s' % (epi_report.clinic, epi_report.clinic.type) }, # Health Unit
            #TODO {"x":4.5*cm, "y":second_row_y, "value":  }, # Health Unit Code
            {"x":16.2*cm, "y":second_row_y, "value":sub_county }, # Sub-County

            #TODO {"x":4.5*cm, "y":third_row_y, "value":  }, # HSD
            {"x":11.2*cm, "y":third_row_y, "value":district  }, # District

            {"x":5.5*cm, "y":footer_row_y, "value":epi_report.completed_on.strftime(DATE_FORMAT)  }, # Submitted on (Date)
            {"x":9.1*cm, "y":footer_row_y, "value":reporters_string, 'size':9 }, # By
            {"x":16.3*cm, "y":footer_row_y, "value":epi_report.receipt, 'size':10  }, # Receipt Number
        ]
        
        # draw the data onto the pdf overlay
        for field in data:
            if field.has_key('size'): c.setFont(FONT, field['size'])
            c.drawString(field['x'],field['y'],unicode(field['value']))
            if field.has_key('size'): c.setFont(FONT, DEFAULT_FONT_SIZE)

    # DISEASE REPORT
    def disease_report():
        disease_order = ['AF','AB','RB','CH','DY','GW','MA','ME','MG','NT','PL','YF','VF','EI']

        # the coordinates of the top left cell in the disease report table
        # coordinates are Cartesian with the (0,0) origin at the lower left corner of the page
        x, y = 13.1*cm, 23.12*cm
        
        # the space between the 'Cases this week' column and the 'Deaths this week' column
        horizontal_space = 3.35*cm

        # space between each row in the table
        vertical_space = .542*cm

        for disease in disease_order:
            disease_observation = epi_report.diseases.diseases.get(disease__code=disease.lower())
            cases = disease_observation.cases
            deaths = disease_observation.deaths
            c.drawRightString(x,y,unicode(cases))
            c.drawRightString(x+horizontal_space,y,unicode(deaths))
            y -= vertical_space
    
    # TEST REPORT
    def test_report():
        x, y = 5.2*cm, 11.7*cm

        # the space between each cell
        horizontal_space = 1.5*cm

        mc = epi_report.malaria_cases
        values = [mc.opd_attendance, mc.suspected_cases, mc.rdt_tests, mc.rdt_positive_tests, mc.microscopy_tests, mc.microscopy_positive, mc.positive_over_five, mc.positive_under_five]
        for value in values:
            c.drawRightString(x,y,unicode(value))
            x += horizontal_space

    # TREAT REPORT
    def treat_report():
        x, y = 5.2*cm, 7*cm

        # the space between each cell
        horizontal_space = 1.5*cm

        mt = epi_report.malaria_treatments
        values = [mt.rdt_positive, mt.rdt_negative, mt.four_months_to_three, mt.three_to_seven, mt.seven_to_twelve, mt.twelve_and_above]
        for value in values:
            c.drawRightString(x,y,unicode(value))
            x += horizontal_space

    # ACT REPORT
    def act_report():
        x, y = 5.0*cm, 3.4*cm

        # the space between each cell
        horizontal_space = 1.2*cm

        act = epi_report.act_consumption
        values = [act.yellow_dispensed, act.yellow_balance, act.blue_dispensed, act.blue_balance, act.brown_dispensed, act.brown_balance, act.green_dispensed, act.green_balance, act.other_act_dispensed, act.other_act_balance]
        for value in values:
            c.drawRightString(x,y,unicode(value))
            x += horizontal_space

    # generate the overlay report
    report_header_footer()
    disease_report()
    test_report()
    treat_report()
    act_report()

    # render and save the pdf overlay to the buffer
    c.showPage()
    c.save()

    # use pdftk to 'stamp' the canvas data containing the data onto the pdf_source. 
    cmd = '/usr/bin/pdftk %s stamp - output -' % PDF_SOURCE
    proc = Popen(cmd,shell=True,stdin=PIPE,stdout=PIPE,stderr=PIPE)
    pdf,cmderr = proc.communicate(buffer.getvalue())

    # We don't need the buffer anymore because the two pdfs have been combined in the string variable pdf
    buffer.close()

    # name the pdf the receipt code, but get rid of the / as those shouldn't be in filenames.
    filename = epi_report.receipt.replace('/','-')

    # first add the headers
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % filename
    
    # then the actual pdf data
    response.write(pdf)

    return response
