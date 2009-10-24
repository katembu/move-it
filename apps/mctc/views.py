#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.webui.utils import render_to_response
from django.db.models import ObjectDoesNotExist, Q
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta
from mctc.forms.general import MessageForm
from pygsm.gsmmodem import GsmModem


from mctc.forms.login import LoginForm
from mctc.shortcuts import as_html, login_required
from mctc.models.logs import log, MessageLog, EventLog
from mctc.models.general import Case
from mctc.models.reports import ReportCHWStatus, ReportAllPatients
from muac.models import ReportMalnutrition
from mrdt.models import ReportMalaria
from locations.models import Location
from libreport.pdfreport import PDFReport
from django.utils.translation import ugettext_lazy as _


from django.template import Template, Context
from django.template.loader import get_template
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect

from tempfile import mkstemp
from datetime import datetime, timedelta, date
import os
import csv
import StringIO

app = {}
app['name'] = "RapidResponse:Health"

def month_end(date):
    for n in (31,30,28):
        try:
            return date.replace(day=n)
        except: pass
    return date

def next_month(date):
    if date.day > 28:
        day     = 28
    else:
        day     = date.day
    if date.month == 12:
        month   = 1
        year    = date.year + 1
    else:
        month   = date.month + 1
        year    = date.year
        
    return date.replace(day=day, month=month, year=year)
    
def day_start(date):
    t   = date.time().replace(hour=0,minute=1)
    return datetime.combine(date.date(), t)

def day_end(date):
    t   = date.time().replace(hour=23,minute=59)
    return datetime.combine(date.date(), t)

def index(request):
    template_name="mctc/index.html"
    has_provider = True
    try:
        mobile = request.user.provider.mobile
        if request.method == "POST":
            messageform = MessageForm(request.POST)
            if messageform.is_valid():
                result = message_users(mobile, **messageform.cleaned_data)
                context["msg"] = result
        else:
            messageform = MessageForm()
    except ObjectDoesNotExist:
        has_provider = False
        messageform = None
    return render_to_response(request, template_name, {
            "message_form": messageform,
            "has_provider": has_provider})
    
    
def message_users(mobile, message=None, groups=None, users=None):
    # problems that might still exist here
    # timeouts in the browser because we have to post all the messages
    # timeouts in the url request filtering up to the above
    recipients = []
    # get all the users
    provider_objects = [ Provider.objects.get(id=user) for user in users ]
    for provider in provider_objects:
        try:
            if provider not in recipients:
                recipients.append(provider)
        except models.ObjectDoesNotExist:
            pass
     # get all the users for the groups
    group_objects = [ Group.objects.get(id=group) for group in groups ]
    for group in group_objects:
        for user in group.user_set.all():
            try:
                if user.provider not in recipients:
                    recipients.append(user.provider)
            except models.ObjectDoesNotExist:
                pass
    port = "ttyUSB0"
    conf = []
    modem = GsmModem(port=port, **conf)
    passed = []
    failed = []
    for recipient in recipients:
        msg = "@%s %s" % (recipient.id, message)
        #cmd = "http://%s:%s/spomc/%s/%s" % (domain, port, mobile, msg)
        try:
            modem.send_sms(recipient, msg)
            passed.append(recipient)
        except IOError:
            # if the mobile number is badly formed and the number regex fails
            # this is the error that is raised
            failed.append(recipient)
    
    results_text = ""
    if not passed and not failed:
        results_text = "No recipients were sent that message."
    elif not failed and passed:
        results_text = "The message was sent to %s recipients" % (len(passed))
    elif failed and passed:
        results_text = "The message was sent to %s recipients, but failed for the following: %s" % (len(passed), ", ".join([ str(f) for f in failed]))
    elif not passed and failed:
        results_text = "No-one was sent that message. Failed for the following: %s" % ", ".join([ str(f) for f in failed])
    return results_text

@login_required
def reports(request):
    template_name="mctc/reports/reports.html"
    
    clinics = Location.objects.filter(type__name="Clinic")
    
    zones = Case.objects.order_by("location").values('location', 'location__name').distinct()
    p = Case.objects.order_by("location").values('reporter', 'reporter__first_name', 'reporter__last_name', 'location').distinct()
    providers = []
    for provider in p:
        tmp = {}
        tmp['id'] = provider['reporter']
        tmp['name'] = provider['reporter__last_name'] + " " + provider['reporter__first_name']
        tmp['zone'] = provider['location']
        providers.append(tmp)  
        
    now = datetime.today()
    first   = Case.objects.order_by('created_at')[:1][0]
    date    = first.created_at

    months=[]
    while ((now - date).days > 0):
        months.append({'id': date.strftime("%m%Y"), 'label': date.strftime("%B %Y"), 'date': date})
        date = next_month(date)
    
    context = {
        "app": app,
        "clinics": clinics,
        "providers": providers,
        "zones": zones,
        "months": months
    }
    return render_to_response(request, template_name, context)

@login_required
def last_30_days(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)
    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()
    
    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today
    
    pdfrpt.setTitle("RapidResponse MVP Kenya: CHW 30 Day Performance Report, from %s to %s"%(duration_start, duration_end))
    
    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.get_providers_by_clinic(duration_start, duration_end, muac_duration_start, clinic)
            c = clinic
            pdfrpt.setTableData(queryset, fields, c.name)
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.get_providers_by_clinic(duration_start, duration_end, muac_duration_start, object_id)
        c = object_id
        
        if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
            file_name = c.name + ".csv"
            file_name = file_name.replace(" ","_").replace("'","")
            return handle_csv(request, queryset, fields, file_name)
        
        pdfrpt.setTableData(queryset, fields, c.name)
    
    return pdfrpt.render()

@login_required
def measles_summary(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)
    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()
    
    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today
    
    #pdfrpt.setTitle("RapidResponse MVP Kenya: CHW 30 Day Performance Report, from %s to %s"%(duration_start, duration_end))
    pdfrpt.setTitle("Measles Campaign Summary")
    if object_id is None:
        clinics = Provider.objects.values('clinic').filter(role=1).distinct()
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.measles_summary(duration_start, duration_end, muac_duration_start, clinic["clinic"])
            c = Facility.objects.filter(id=clinic["clinic"])[0]
            pdfrpt.setTableData(queryset, fields, c.name)
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
        queryset, fields = ReportCHWStatus.measles_summary(duration_start, duration_end, muac_duration_start, object_id)
        c = Facility.objects.filter(id=object_id)[0]
        
        if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
            file_name = c.name + ".csv"
            file_name = file_name.replace(" ","_").replace("'","")
            return handle_csv(request, queryset, fields, file_name)
        
        pdfrpt.setTableData(queryset, fields, c.name)
    
    return pdfrpt.render()

@login_required
def patients_by_chw(request, object_id=None, per_page="0", rformat="pdf"):
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(False)
    pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    
    if object_id is None:        
        if request.POST and request.POST['zone']:
            providers = Case.objects.filter(zone=request.POST['zone']).values('provider', 'zone__name').distinct()
            per_page = "1"
        else:
            providers = Case.objects.order_by("zone").values('provider', 'zone__name').distinct()
        for provider in providers:
            queryset, fields = ReportAllPatients.by_provider(provider['provider'])
            if queryset:
                c = Provider.objects.get(id=provider["provider"])
                pdfrpt.setTableData(queryset, fields, provider['zone__name']+": "+c.get_name_display())
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                    pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        
        queryset, fields = ReportAllPatients.by_provider(object_id)
        if queryset:
            c = Provider.objects.get(id=object_id)
            
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = c.get_name_display() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c.get_name_display())
    
    return pdfrpt.render()

def handle_csv(request, queryset, fields, file_name):
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    for row in queryset:
        ctx = Context({"object": row })
        if not header:
            csvio.writerow([f["name"] for f in fields])
            header = True
        values = [ Template(h["bit"]).render(ctx) for h in fields ]
        csvio.writerow(values)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response


@login_required
def report_view(request, report_name, object_id=None):
    part = report_name.partition('_')
    if part.__len__() == 3:
        report_name = part[0]
        format  = part[2]
    else:
        format  = 'csv'
        
    if report_name  == 'monitoring':
        month   = datetime(int(object_id[2:6]), int(object_id[:2]), 1)
        filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': month.strftime("%B-%Y"), 'ext':format}
        return report_monitoring_csv(request, object_id, filename)
    if report_name == 'measlessummary':
        return measles_mini_summary_csv(request, "measles_summary.csv")
    if report_name == "all-patient":        
        filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': datetime.today().strftime("%Y-%m-%d"), 'ext':format}
        if object_id == "1":
            return all_providers_list_pdf(request, filename,True)
        else:
            return all_providers_list_pdf(request, filename)
    if report_name == "chwstatus":
        return chwstatus_pdf(request)
    queryset, fields = build_report(report_name, object_id)
    filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': datetime.today().strftime("%Y-%m-%d"), 'ext':format}
    
    return eval("handle_%s" % format)(request, queryset, fields, filename)

def measles_mini_summary_csv(request, file_name):
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    summary =  ReportCHWStatus.measles_mini_summary()
    rows = []
    row = []
    row.append("Facility")
    row.append("No. Vaccinated")
    row.append("No. Eligible")
    row.append("%")
    rows.append(row)
    for info in summary:
        info["percentage"] = round(float(float(info["vaccinated_cases"])/float(info["eligible_cases"]))*100, 2); 
        
        row = []
        row.append(u"%(clinic)s"%info)
        row.append(u"%(vaccinated_cases)s"%info)
        row.append(u"%(eligible_cases)s"%info)
        row.append(u"%(percentage)s%%"%info)
        rows.append(row)
    # Write rows on CSV
    for row in rows:
        csvio.writerow([cell for cell in row])    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response

def report_monitoring_csv(request, object_id, file_name):
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    
    # parse parameter
    month   = datetime(int(object_id[2:6]), int(object_id[:2]), 1)
    
    # Header Line (days of month)
    eom = month_end(month)
    days= range(-1, eom.day + 1)
    days.remove(0)
    gdays   = days # store that good list
    csvio.writerow([d.__str__().replace("-1", month.strftime("%B")) for d in days])
    
    # Initialize Rows
    sms_num     = ["# SMS Sent"]
    sms_process = ["Processed"]
    sms_refused = ["Refused"]
    
    chw_tot     = ["Total CHWs in System"]
    chw_reg     = ["New CHWs Registered"]
    chw_reg_err = ["Failed Registration"]

    chw_on      = ["Active CHWS"]

    patient_reg = ["New Patients Registered"]
    patient_reg_err = ["Registration Failed"]

    malaria_tot = ["Total Malaria Reports"]
    malaria_err = ["Malaria Reports (Failed)"]

    malaria_pos = ["Malaria Tests Positive"]
    bednet_y_pos= ["Bednet Yes"]
    bednet_n_pos= ["Bednet No"]
    malaria_neg = ["Malaria Tests False"]
    bednet_y_neg= ["Bednet Yes"]
    bednet_n_neg= ["Bednet No"]

    malnut_tot  = ["Total Malnutrition Reports"]
    malnut_err  = ["Malnutrition Reports (Failed)"]

    samp_tot     = ["Total SAM+"]
    sam_tot     = ["Total SAM"]
    mam_tot     = ["Total MAM"]

    samp_new    = ["New SAM+"]
    sam_new     = ["New SAM"]
    mam_new     = ["New MAM"]

    user_msg    = ["User Messaging"]
    
    blank       = []

    # List all rows    
    rows    = [blank, sms_num, sms_process, sms_refused, blank, chw_tot, chw_reg, chw_reg_err, blank,
    chw_on, blank, patient_reg, patient_reg_err, blank, malaria_tot, malaria_err, blank, 
    malaria_pos, bednet_y_pos, bednet_n_pos, malaria_neg, bednet_y_neg, bednet_n_neg, blank,
    malnut_tot, malnut_err, blank, samp_tot, sam_tot, mam_tot, blank, samp_new, sam_new, mam_new, blank, user_msg]
    
    # Loop on days
    for d in gdays:
        if d == -1: continue
        ref_date    = datetime(month.year, month.month, d)
        morning     = day_start(ref_date)
        evening     = day_end(ref_date)
        
        # Number of SMS Sent
        sms_num.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening).count())
        
        # Number of SMS Processed
        sms_process.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, was_handled=True).count())
        
        # Number of SMS Refused
        sms_refused.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, was_handled=False).count())
        
        # Total # of CHW in System
        chw_tot.append(Provider.objects.filter(role=Provider.CHW_ROLE,user__in=User.objects.filter(date_joined__lte=ref_date)).count())
        
        # New Registered CHW
        chw_reg.append(Provider.objects.filter(role=Provider.CHW_ROLE,user__in=User.objects.filter(date_joined__gte=morning, date_joined__lte=evening)).count())
        
        # Failed CHW Registration
        chw_reg_err.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="provider_registered").count() - EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="confirmed_join").count())
        
        # Active CHWs
        a = Case.objects.filter(created_at__gte=morning, created_at__lte=evening)
        a.query.group_by = ['mctc_case.provider_id']
        chw_on.append(a.__len__())
        
        # New Patient Registered
        patient_reg.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="patient_created").count())
        
        # Failed Patient Registration
        patient_reg_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__startswith="new").count() - patient_reg[-1])
        
        # Total Malaria Reports
        malaria_tot.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="mrdt_taken").count())
        
        # Failed Malaria Reports
        malaria_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__startswith="mrdt").count() - malaria_tot[-1])
        
        # Malaria Test Positive
        malaria_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True).count())
        
        # Malaria Positive with Bednets
        bednet_y_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True, bednet=True).count())
        
        # Malaria Positive without Bednets
        bednet_n_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True, bednet=False).count())
        
        # Malaria Test Negative
        malaria_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False).count())
        
        # Malaria Negative with Bednets
        bednet_y_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False, bednet=True).count())
        
        # Malaria Negative without Bednets
        bednet_n_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False, bednet=False).count())
        
        # Total Malnutrition Reports
        malnut_tot.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="muac_taken").count())
        
        # Failed Malnutrition Reports
        malnut_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__startswith="muac").count() - malnut_tot[-1])
        
        # Total SAM+
        samp_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.SEVERE_COMP_STATUS).count())
        
        # Total SAM
        sam_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.SEVERE_STATUS).count())
        
        # Total MAM
        mam_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.MODERATE_STATUS).count())
        
        # New SAM+
        samp_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.SEVERE_COMP_STATUS).count())
        
        # New SAM
        sam_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.SEVERE_STATUS).count())
        
        # New MAM
        mam_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.MODERATE_STATUS).count())
        
        # User Messaging
        user_msg.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__startswith="@").count())

    # Write rows on CSV
    for row in rows:
        csvio.writerow([cell for cell in row])
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response

@login_required
def measles(request, object_id=None, per_page="0", rformat="pdf"):
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(False)
    #pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    pdfrpt.setTitle("Measles Campaign")
    if object_id is None:        
        if request.POST and request.POST['zone']:
            providers = Case.objects.filter(zone=request.POST['zone']).values('provider', 'zone__name').distinct()
            per_page = "1"
        else:
            providers = Case.objects.order_by("zone").values('provider', 'zone__name').distinct()
        for provider in providers:
            queryset, fields = ReportAllPatients.measles_by_provider(provider['provider'])
            if queryset:
                c = Provider.objects.get(id=provider["provider"])
                pdfrpt.setTableData(queryset, fields, provider['zone__name']+": "+c.get_name_display()+" (sms format: `MEASLES +PID +PID +PID`)")
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                    pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        
        queryset, fields = ReportAllPatients.measles_by_provider(object_id)
        if queryset:
            c = Provider.objects.get(id=object_id)
            
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = c.get_name_display() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c.get_name_display()+" (sms format: `MEASLES +PID +PID +PID`)")
    
    return pdfrpt.render()

@login_required
def malnut(request, object_id=None, per_page="0", rformat="pdf"):
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    #pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    pdfrpt.setTitle("RapidResponse MVP Kenya: Malnutrition Report")
    if object_id is None:        
        if request.POST and request.POST['zone']:
            providers = Case.objects.filter(zone=request.POST['zone']).values('provider', 'zone__name').distinct()
            per_page = "1"
        else:
            providers = Case.objects.order_by("zone").values('provider', 'zone__name').distinct()
        #for provider in providers:
        queryset, fields = ReportAllPatients.malnut_by_provider()
        if queryset:
            
            pdfrpt.setTableData(queryset, fields, "")
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
            
            
        
        queryset, fields = ReportAllPatients.malnut_by_provider(object_id)
        if queryset:
            c = Provider.objects.get(id=object_id)
            
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = c.get_name_display() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c.get_name_display())
    
    return pdfrpt.render()

@login_required
def malaria(request, object_id=None, per_page="0", rformat="pdf"):
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    #pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    pdfrpt.setTitle("RapidResponse MVP Kenya: Malaria Report")
    if object_id is None:        
        if request.POST and request.POST['zone']:
            providers = Case.objects.filter(zone=request.POST['zone']).values('provider', 'zone__name').distinct()
            per_page = "1"
        else:
            providers = Case.objects.order_by("zone").values('provider', 'zone__name').distinct()
        #for provider in providers:
        queryset, fields = ReportAllPatients.malaria_by_provider()
        if queryset:
            pdfrpt.setTableData(queryset, fields, "")
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        
        queryset, fields = ReportAllPatients.malaria_by_provider(object_id)
        if queryset:
            c = Provider.objects.get(id=object_id)
            
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = c.get_name_display() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c.get_name_display())
    
    return pdfrpt.render()
def trend(request, object_id=None, per_page="0", rformat="pdf"):
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(False)
    pdfrpt.setTitle("RapidResponse MVP Kenya: Malnutrition Trend by Case Report")
    
    if object_id is None:        
        queryset, fields = ReportAllPatients.malnut_trend_by_provider()
        if queryset:
            pdfrpt.setTableData(queryset, fields, "")
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        
        queryset, fields = ReportAllPatients.malnut_trend_by_provider(object_id)
        if queryset:
            c = Provider.objects.get(id=object_id)
            
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = c.get_name_display() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c.get_name_display())
    
    return pdfrpt.render()
