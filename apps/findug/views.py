#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import datetime, timedelta

from rapidsms.webui.utils import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from models import *
from apps.findug.utils import *
from apps.locations.models import *

from apps.libreport.pdfreport import PDFReport
from apps.libreport.csvreport import CSVReport

# Imports for epidemiological_report_pdf
from django.http import HttpResponse, Http404
from reportlab.pdfgen import canvas
from subprocess import Popen, PIPE
from cStringIO import StringIO
from reportlab.lib.units import cm

# import the settings so we can access DATE_FORMAT
from django.conf import settings

from tables import *
import django_tables as tables
from django.core.paginator import Paginator

from django.db.models import Sum, Count

class Scope:
    def __init__(self, location):
        self.is_global = location == None
        self.location = location
        self.district_id = -1

    def __unicode__(self):
        if self.location == None:
                return u'All'
        else:
            return self.location.name

    def districts(self):
        if self.is_global:
            return Location.objects.filter(type__name='district')
        else:
            return [self.location.district]

    def set_district(self, district_id):
        self.district_id = district_id
        if district_id == -1:
            self.location = None
        else:
            try:
                self.location = Location.objects.get(id=district_id)
            except Location.DoesNotExist:
                self.location = None

    def health_units(self):
        ''' Return the health units within scope location '''
        if self.location == None:
            return HealthUnit.objects.all()
        else:
            return HealthUnit.list_by_location(self.location)

    def health_workers(self):
        ''' Return the reporters with health worker role within the health units of the scope '''

        health_units = self.health_units()
        hws = []
        for hw in Reporter.objects.filter(role__code='hw'):
            if HealthUnit.by_location(hw.location) in health_units:
                hws.append(hw)
        return hws

def define_scope(f):
    """
    Decorator to define the scope for any webuser
    """
    def _inner(req, *args, **kwargs):
        webuser = WebUser.by_user(req.user)
        scope = Scope(webuser.location)
        if scope.is_global:
            if req.method == 'POST' and req.POST.has_key('district'):
                req.session['district'] = int(req.POST['district'])
            scope.set_district(req.session.get('district', -1))
        return f(req, scope, *args, **kwargs)
    return _inner

@login_required
@define_scope
def index(req, scope):
    ''' Display Dashboard '''

    summary = {}
    if datetime.today().weekday() == 6:
        period = ReportPeriod.objects.latest()
    else:
        period = ReportPeriod.from_day(datetime.today())
    summary['period'] = period    
    summary['total_units'] = len(scope.health_units())
    summary['up2date'] = len(filter(lambda hc: hc.up2date(), scope.health_units()))
    summary['missing'] = summary['total_units'] - summary['up2date']

    recent = []
    for report in EpidemiologicalReport.objects.filter(_status=EpidemiologicalReport.STATUS_COMPLETED, clinic__in=scope.health_units()).order_by('-completed_on')[:10]:
        recent.append({
            'id':report.id,
            'date':report.completed_on.strftime("%a %H:%M"), 
            'by': ('%s %s' % (report.completed_by().first_name, report.completed_by().last_name)).title(),
            'by_id':report.completed_by().id,
            'clinic':report.clinic,
            'clinic_id':report.clinic.id
        })
    return render_to_response(req, 'findug/index.html', {'summary': summary, 'scope':scope, 'recent':recent})

@login_required
@define_scope
def map(req, scope):
    ''' Map view '''

    if datetime.today().weekday() == 6:
        previous_period = ReportPeriod.objects.latest()
    else:
        previous_period = ReportPeriod.from_day(datetime.today())

    all = []
    for location in scope.health_units():
        loc = {}
        loc['obj'] = location
        loc['name'] = unicode(location)
        loc['type'] = location.type.name.lower().replace(' ','')
        act_reports = ACTConsumptionReport.objects.filter(reporter__location=location).filter(period=previous_period)
        if not act_reports: 
            loc['act_unknown'] = True
        else:
            rpt = act_reports[0]
            if rpt.yellow_balance: loc['yellow'] = True
            if rpt.blue_balance: loc['blue'] = True
            if rpt.brown_balance: loc['brown'] = True
            if rpt.green_balance: loc['green'] = True
             
        all.append(loc)

    return render_to_response(req, 'findug/map.html', {'scope':scope, 'locations': all})

@login_required
@define_scope
def health_units_view(req, scope):
    ''' List health units in scope with links to individual pages '''

    locations = scope.health_units()

    if req.GET.get('filter') == 'missing':
        locations = filter(lambda hc: not hc.up2date(), locations)
    elif req.GET.get('filter') == 'current':
        locations = filter(lambda hc: hc.up2date(), locations)

    if datetime.today().weekday() == 6:
        previous_period = ReportPeriod.objects.latest()
    else:
        previous_period = ReportPeriod.from_day(datetime.today())

    today = datetime.today()
    all = []
    for location in locations:
        loc = {}
        loc['pk']       = location.pk
        loc['name']     = location.name
        loc['hctype']   = location.type.name
        loc['code']     = location.code.upper()
        loc['hsd']      = unicode(location.hsd)
        loc['reporters']= len(Reporter.objects.filter(location=location.location_ptr))
        last            = EpidemiologicalReport.last_completed_by_clinic(location)
        if last:
            # the last column is the visible, nicely formated date
            loc['last'] = last.completed_on.strftime(settings.DATE_FORMAT)
            loc['last_pk'] = last.pk

            # the last_sost is not visible, it is used to sort the date column
            loc['last_sort'] = last.completed_on
            if last.period == previous_period:
                loc['last_color'] = 'green'
            elif last.period == ReportPeriod.objects.all()[1]:
                loc['last_color'] = 'yellow'
            else:
                loc['last_color'] = 'red'
               
        else: #the health unit has not filed a report.
            loc['last']         = 'N / A'
            loc['last_color']   = 'red'
            # if they never filed a report, we need to set last_sort to some arbitrarily old date to make sure it sorts at the bottom]
            # if django templates compared None objects as they should, we wouldn't have to do this
            loc['last_sort'] = datetime(year=2000,month=1,day=1)


        all.append(loc)
    table = HealthUnitsTable(all, order_by=req.GET.get('sort'))
    #table.paginate(Paginator, 10, page=1, orphans=2)

    # sort by date, descending
    return render_to_response(req, 'findug/health_units.html', {'scope':scope, 'table': table, 'filter':req.GET.get('filter')})

@login_required
def health_unit_view(req, health_unit_id):
    ''' Displays a summary of location activities and history '''

    RECENT_REPORTS=5

    health_unit    = HealthUnit.objects.get(id=health_unit_id)
    reporters = Reporter.objects.filter(location=health_unit.location_ptr)
    all = []
    for reporter in reporters:
        rep = {}
        rep['alias']    = reporter.alias
        rep['name']     = reporter.full_name().title()
        if reporter.connection():
            rep['contact']  = reporter.connection().identity
        else:
            rep['contact']  = ''
        all.append(rep)
    reporters_table = HWReportersTable(all)
    del(reporters_table.base_columns['hu'])

    webuser = WebUser.by_user(req.user)
    locations = webuser.health_units()

    periods = ReportPeriod.objects.all().order_by('-end_date')[:RECENT_REPORTS]
    rows = []
    for period in periods:
        row={}
        row['date'] = period.start_date
        row.update(DiseasesReport.aggregate_report(health_unit, [period]))
        rows.append(row)
    diseases_table              = DiseasesReportTable(rows)
    diseases_table.base_columns.insert(0,'date', tables.Column(verbose_name=u"Date Period", sortable=False))

    rows = []    
    for period in periods:
        row={}
        row['date'] = period.start_date
        row.update(MalariaCasesReport.aggregate_report(health_unit, [period]))
        rows.append(row)
    cases_table              = CasesReportTable(rows)
    cases_table.base_columns.insert(0,'date', tables.Column(verbose_name=u"Date Period", sortable=False))

    rows = []    
    for period in periods:
        row={}
        row['date'] = period.start_date
        row.update(MalariaTreatmentsReport.aggregate_report(health_unit, [period]))
        rows.append(row)

    treatments_table            = TreatmentsReportTable(rows)
    treatments_table.base_columns.insert(0,'date', tables.Column(verbose_name=u"Date Period", sortable=False))

    rows = []    
    for period in periods:
        row={}
        row['date'] = period.start_date
        row.update(ACTConsumptionReport.aggregate_report(health_unit, [period]))
        rows.append(row)

    act_table            = ACTReportTable(rows)
    act_table.base_columns.insert(0,'date', tables.Column(verbose_name=u"Date Period", sortable=False))

    context_dict = {
        'health_unit':      health_unit,
        'reporters_table':  reporters_table,
        'diseases_table':   diseases_table,
        'diseases':         Disease.ug_diseases(),
        'cases_table':      cases_table,
        'treatments_table': treatments_table,
        'act_table':        act_table,
    }
    return render_to_response(req, 'findug/health_unit.html', context_dict)

@login_required
@define_scope
def report_view(req, scope):

    try:
        start_period = ReportPeriod.objects.get(pk=req.GET.get('start',ReportPeriod.objects.latest().id))
    except (ReportPeriod.DoesNotExist, ValueError):
        start_period = ReportPeriod.objects.latest()
    try:
        end_period = ReportPeriod.objects.get(pk=req.GET.get('end',start_period.id))
    except (ReportPeriod.DoesNotExist, ValueError):
        end_period = start_period

    periods = ReportPeriod.list_from_boundries(start_period, end_period)
    #periods = ReportPeriod.objects.all()

    if len(periods) == 1:
        dates = {'start':periods[0].start_date, 'end':periods[0].end_date}
    elif len(periods) > 1:
        dates = {'start':periods.reverse()[0].start_date, 'end':periods[0].end_date}

    grp = req.GET.get('grp')

    if req.GET.get('r') == 'diseases':
        report              = 'diseases'
        cls                 = DiseasesReport
        table_class         = DiseasesReportTable
        table_name          = 'diseases_table'
        report_title        = _(u'Diseases')
        include_template    = 'findug/diseases_report_include.html'
    elif req.GET.get('r') == 'cases':
        report              = 'cases'
        cls                 = MalariaCasesReport
        table_class         = CasesReportTable
        table_name          = 'cases_table'
        report_title        = _(u'Malaria Cases')
        include_template    = 'findug/cases_report_include.html'
    elif req.GET.get('r') == 'treat':
        report              = 'treat'
        cls                 = MalariaTreatmentsReport
        table_name          = 'treatments_table'
        table_class         = TreatmentsReportTable
        report_title        = _(u'Malaria Treatments')
        include_template    = 'findug/treatments_report_include.html'
    elif req.GET.get('r') == 'act':
        report              = 'act'
        cls                 = ACTConsumptionReport
        table_name          = 'act_table'
        table_class         = ACTReportTable
        report_title        = _(u'ACT Consumption')
        include_template    = 'findug/act_report_include.html'
    else:
        raise Http404

    rows=[]

    if grp in ['parish','subcounty','county','hsd','district','type']:
        groups = []
        for hu in scope.health_units():
            groups.append(eval('hu.%s' % grp))
        groups = set(groups)
        for group in groups:
            row={}
            row['grp'] = unicode(group)
            if grp == 'type':
                row.update(cls.aggregate_report(scope.location, periods, group))
            else:
                row.update(cls.aggregate_report(group, periods))
            rows.append(row)
        table = table_class(rows)
        if    grp == 'type': title = 'Health Unit Type'
        elif  grp == 'hsd':  title = 'Health Sub District'
        else:                title = grp.title()
        table.base_columns.insert(0,'grp',tables.Column(verbose_name=title, sortable=True))
    else:
        for hu in scope.health_units():
            row={}
            row['hu'] = unicode(hu)
            row['hu_pk'] = hu.id
            row.update(cls.aggregate_report(hu, periods))
            rows.append(row)
        table = table_class(rows)
        table.base_columns.insert(0,'hu',tables.Column(verbose_name=u"Health Unit"))
        table.base_columns.insert(1,'hu_pk', tables.Column(visible=False, sortable=False))

    table.order_by=order_by=req.GET.get('sort')
    table.update

    print grp
    if len(periods) > 1 or grp in ['parish','subcounty','county','hsd','district','type']:
        aggregate = True
    else:
        aggregate = False

    context_dict = {
            'report'            : report,
            'scope'             : scope, 
            table_name          : table,
            'dates'             : dates,
            'report_title'      : report_title,
            'include_template'  : include_template,
            'grouping'          : grp,
            'start'             : start_period.id,
            'end'               : end_period.id,
            'aggregate'         : aggregate,
    }
    if report == 'diseases': context_dict['diseases'] = Disease.ug_diseases()
    return render_to_response(req, 'findug/report.html', context_dict)

@login_required
@define_scope
def reports_view(req, scope):
    ''' Show available reports '''

    return render_to_response(req, 'findug/reports.html', {'scope':scope, 'periods':ReportPeriod.objects.all()})


@login_required
@define_scope
def reporters_view(req, scope):
    ''' Displays a list of reporters '''

    reporters = scope.health_workers()

    all = []
    for reporter in reporters:
        rep = {}
        rep['alias']    = reporter.alias
        rep['name']     = reporter.full_name().title()
        rep['hu']       = unicode(HealthUnit.by_location(reporter.location))
        rep['hu_pk']    = HealthUnit.by_location(reporter.location).pk
        if reporter.connection():
            rep['contact']  = reporter.connection().identity
        else:
            rep['contact']  = ''
        all.append(rep)

    table = HWReportersTable(all, order_by=req.GET.get('sort'))

    return render_to_response(req, 'findug/reporters.html', { "scope":scope, "table": table})

@login_required
def reporter_view(req, reporter_id):
    ''' Displays a summary of his activities and history '''

    reporter    = Reporter.objects.get(id=reporter_id)

    return render_to_response(req, 'findug/reporter.html', { "reporter": reporter})

def epidemiological_report(req, report_id):
    DATE_FORMAT = settings.DATE_FORMAT
    epi_report = EpidemiologicalReport.objects.get(id=report_id)

    headers = {}
    headers['date']  =   {'label':'Date', 'value':datetime.today().strftime(DATE_FORMAT)}
    headers['for']   =   {'label':'For Period (Date)', 'value':epi_report.period.start_date.strftime(DATE_FORMAT)}
    headers['to']    =   {'label':'To (Date)', 'value':epi_report.period.end_date.strftime(DATE_FORMAT)}
    headers['hu']    =   {'label':'Health Unit', 'value':epi_report.clinic}
    headers['huc']   =   {'label':'Health Unit Code', 'value':re.sub(r'^\D+','',epi_report.clinic.code)}
    headers['sc']    =   {'label':'Sub-County', 'value':epi_report.clinic.subcounty}
    headers['hsd']   =   {'label':'HSD', 'value':epi_report.clinic.hsd}

    #Remove unnecessary ' District'
    district = epi_report.clinic.district.name.replace(' District','')
    headers['dis']   =   {'label':'District', 'value':district}

    disease_order = ['AF','AB','RB','CH','DY','GW','MA','ME','MG','NT','PL','YF','VF','EI']
    diseases = []
    number = 0
    for disease in disease_order:
        dis = {}
        number += 1
        disease_observation = epi_report.diseases.diseases.get(disease__code=disease.lower())
        dis['number']   = number
        dis['name']     = disease_observation.disease
        dis['cases']    = '%02d' % disease_observation.cases
        dis['deaths']   = '%02d' % disease_observation.deaths
        diseases.append(dis)

    mc = epi_report.malaria_cases
    test = {}
    test['opd']     = {'label':mc._meta.get_field('_opd_attendance').verbose_name, 'value':'%02d' % mc.opd_attendance}
    test['susp']    = {'label':mc._meta.get_field('_suspected_cases').verbose_name, 'value':'%02d' % mc.suspected_cases}
    test['rdt']     = {'label':mc._meta.get_field('_rdt_tests').verbose_name, 'value':'%02d' % mc.rdt_tests}
    test['rdtp']    = {'label':mc._meta.get_field('_rdt_positive_tests').verbose_name, 'value':'%02d' % mc.rdt_positive_tests}
    test['mic']     = {'label':mc._meta.get_field('_microscopy_tests').verbose_name, 'value':'%02d' % mc.microscopy_tests}
    test['micp']    = {'label':mc._meta.get_field('_microscopy_positive').verbose_name, 'value':'%02d' % mc.microscopy_positive}
    test['un5']     = {'label':mc._meta.get_field('_positive_under_five').verbose_name, 'value':'%02d' % mc.positive_under_five}
    test['ov5']     = {'label':mc._meta.get_field('_positive_over_five').verbose_name, 'value':'%02d' % mc.positive_over_five}
 
    mt = epi_report.malaria_treatments
    treat = {}
    treat['rdtp']   = {'label':mt._meta.get_field('_rdt_positive').verbose_name, 'value':'%02d' % mt.rdt_positive}
    treat['rdtn']   = {'label':mt._meta.get_field('_rdt_negative').verbose_name, 'value':'%02d' % mt.rdt_negative}
    treat['4m']     = {'label':mt._meta.get_field('_four_months_to_three').verbose_name, 'value':'%02d' % mt.four_months_to_three}
    treat['3y']     = {'label':mt._meta.get_field('_three_to_seven').verbose_name, 'value':'%02d' % mt.three_to_seven}
    treat['7y']     = {'label':mt._meta.get_field('_seven_to_twelve').verbose_name, 'value':'%02d' % mt.seven_to_twelve}
    treat['12y']    = {'label':mt._meta.get_field('_twelve_and_above').verbose_name, 'value':'%02d' % mt.twelve_and_above}

    ar = epi_report.act_consumption
    act={}
    act['yd']   = {'label':ar._meta.get_field('_yellow_dispensed').verbose_name, 'value':'%02d' % ar.yellow_dispensed}
    act['yb']   = {'label':ar._meta.get_field('_yellow_balance').verbose_name, 'value':'%02d' % ar.yellow_balance}
    act['bld']  = {'label':ar._meta.get_field('_blue_dispensed').verbose_name, 'value':'%02d' % ar.blue_dispensed}
    act['blb']  = {'label':ar._meta.get_field('_blue_balance').verbose_name, 'value':'%02d' % ar.blue_balance}
    act['brd']  = {'label':ar._meta.get_field('_brown_dispensed').verbose_name, 'value':'%02d' % ar.brown_dispensed}
    act['brb']  = {'label':ar._meta.get_field('_brown_balance').verbose_name, 'value':'%02d' % ar.brown_balance}
    act['gd']   = {'label':ar._meta.get_field('_green_dispensed').verbose_name, 'value':'%02d' % ar.green_dispensed}
    act['gb']   = {'label':ar._meta.get_field('_green_balance').verbose_name, 'value':'%02d' % ar.green_balance}
    act['od']   = {'label':ar._meta.get_field('_other_act_dispensed').verbose_name, 'value':'%02d' % ar.other_act_dispensed}
    act['ob']   = {'label':ar._meta.get_field('_other_act_balance').verbose_name, 'value':'%02d' % ar.other_act_balance}

    footer = {}
    footer['date']      = {'label':'Submitted on (Date)', 'value':epi_report.completed_on.strftime(settings.DATE_FORMAT)}
    footer['by']        = {'label':'By', 'value':epi_report.completed_by().full_name().title()}
    footer['receipt']  = {'label':'Receipt Number', 'value':epi_report.receipt}
    
    report = {}
    report['diseases']  = diseases
    report['headers']   = headers
    report['test']      = test
    report['treat']     = treat
    report['act']       = act
    report['remarks']   = epi_report.remarks
    report['footer']    = footer

    return render_to_response(req, 'findug/epidemiological_report.html', {'report':report})

@login_required
def epidemiological_report_pdf(req, report_id):
    ''' Generates filled-in pdf copy of a completed EpidemiologicalReport object '''

    # Static source pdf to be overlayed
    PDF_SOURCE = 'apps/findug/static/epi_form_20091027.pdf'

    DATE_FORMAT = settings.DATE_FORMAT

    DEFAULT_FONT_SIZE = 11
    FONT = 'Courier-Bold'

    # A simple function to return a leading 0 on any single digit int.  
    def double_zero(value):
        try:
            return '%02d' % value
        except TypeError:
            return value

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
        remarks_row_y   =  1.70*cm

        #Remove unnecessary ' District'
        district = epi_report.clinic.district.name.replace(' District','')

        #Remove unnecessary ' HSD'
        hsd = epi_report.clinic.hsd.name.replace(' HSD','')

        # remove unncessary ' SC'
        sub_county = epi_report.clinic.subcounty.name.replace(' SC','')

        # A list containing dictionaries of each field in the header and footer
        # Each item in the list is a dictionary with the x and y coords and the value of the data
        data = [
            {"x":3.5*cm, "y":first_row_y, "value":datetime.today().strftime(DATE_FORMAT)}, # Date
            {"x":10.6*cm, "y":first_row_y, "value":epi_report.period.start_date.strftime(DATE_FORMAT)}, # For Period (Date)
            {"x":16.0*cm, "y":first_row_y, "value":epi_report.period.end_date.strftime(DATE_FORMAT)}, # To (Date)

            {"x":3.8*cm, "y":second_row_y, "value":epi_report.clinic }, # Health Unit
            {"x":12.0*cm, "y":second_row_y, "value":re.sub(r'^\D+','',epi_report.clinic.code)  }, # Health Unit Code
            {"x":15.9*cm, "y":second_row_y, "value":sub_county }, # Sub-County

            {"x":3.5*cm, "y":third_row_y, "value":hsd  }, # HSD
            {"x":11.2*cm, "y":third_row_y, "value":district  }, # District

            {"x":5.5*cm, "y":footer_row_y, "value":epi_report.completed_on.strftime(DATE_FORMAT)  }, # Submitted on (Date)
            {"x":9.1*cm, "y":footer_row_y, "value":epi_report.completed_by().full_name().title() }, # By
            {"x":16.3*cm, "y":footer_row_y, "value":epi_report.receipt, 'size':10  }, # Receipt Number
        ]

        if epi_report.remarks: 
            data.append({"x":2.0*cm, "y":remarks_row_y, "value":'Remarks: %s' % epi_report.remarks})  
        
        # draw the data onto the pdf overlay
        for field in data:
            if field.has_key('size'): c.setFont(FONT, field['size'])
            c.drawString(field['x'],field['y'],unicode(double_zero(field['value'])))
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
            c.drawRightString(x,y,unicode(double_zero(cases)))
            c.drawRightString(x+horizontal_space,y,unicode(double_zero(deaths)))
            y -= vertical_space
    
    # TEST REPORT
    def test_report():
        x, y = 5.2*cm, 11.7*cm

        # the space between each cell
        horizontal_space = 1.5*cm

        mc = epi_report.malaria_cases
        values = [mc.opd_attendance, mc.suspected_cases, mc.rdt_tests, mc.rdt_positive_tests, mc.microscopy_tests, mc.microscopy_positive, mc.positive_under_five, mc.positive_over_five]
        for value in values:
            c.drawRightString(x,y,unicode(double_zero(value)))
            x += horizontal_space

    # TREAT REPORT
    def treat_report():
        x, y = 5.2*cm, 7*cm

        # the space between each cell
        horizontal_space = 1.5*cm

        mt = epi_report.malaria_treatments
        values = [mt.rdt_positive, mt.rdt_negative, mt.four_months_to_three, mt.three_to_seven, mt.seven_to_twelve, mt.twelve_and_above]
        for value in values:
            c.drawRightString(x,y,unicode(double_zero(value)))
            x += horizontal_space

    # ACT REPORT
    def act_report():
        x, y = 5.0*cm, 3.4*cm

        # the space between each cell
        horizontal_space = 1.2*cm

        act = epi_report.act_consumption
        values = [act.yellow_dispensed, act.yellow_balance, act.blue_dispensed, act.blue_balance, act.brown_dispensed, act.brown_balance, act.green_dispensed, act.green_balance, act.other_act_dispensed, act.other_act_balance]
        for value in values:
            c.drawRightString(x,y,unicode(double_zero(value)))
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

