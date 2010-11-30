#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os
import re
from datetime import date, timedelta, datetime
from urllib import urlencode

from rapidsms.webui.utils import render_to_response
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.utils.translation import gettext_lazy as _, activate
from django.utils import simplejson
from django.template import Template, Context, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, UserManager, Group
from django import forms
from django.db.models import F, Q
from reporters.models import PersistantConnection, PersistantBackend
from locations.models import Location

from childcount.models import Patient, CHW, Configuration, Clinic
from childcount.fields import PatientForm
from childcount.models.ccreports import TheCHWReport, ClinicReport, ThePatient
from childcount.models.ccreports import MonthSummaryReport
from childcount.models.ccreports import GeneralSummaryReport
from childcount.models.ccreports import SummaryReport, WeekSummaryReport
from childcount.reports import report_framework
from childcount.utils import clean_names

form_config = Configuration.objects.get(key='dataentry_forms').value
cc_forms = re.split(r'\s*,*\s*', form_config)


@login_required
def dataentry(request):
    ''' displays Data Entry U.I. '''

    ''' Make default date in the future so that DE clerk is forced
    to manually select a date. '''
    today = (date.today() + timedelta(1)).strftime("%Y-%m-%d")
    chws = CHW.objects.filter(is_active=True)
    try:
        chw = CHW.objects.get(id=request.user.id)
    except CHW.DoesNotExist:
        return redirect(index)
    return render_to_response(request, 'childcount/data_entry.html', \
                              {'chws': chws, 'today': today, \
                               'chw': chw, 'forms': cc_forms})

@login_required
def form(request, formid):
    ''' sends form_id according to user's language '''

    chw = CHW.objects.get(id=request.user.id)
    activate(chw.language)
    form = loader.get_template('childcount/forms/%s.json' % formid)\
                              .render(Context({}))

    return HttpResponse(form, mimetype="application/json")

@login_required
def index(request):
    '''Index page '''
    template_name = "childcount/index.html"
    title = "ChildCount+"

    info = {}

    info.update({"title": title})
    info.update({'risk': nutrition_png(request)})
    info.update(clinic_report(request))
    clinics = Location.objects.all()
    info.update({'sms': sms_png(request)})
    #info.update({'clinics': clinics})
    info.update({'atrisk': TheCHWReport.total_at_risk(), \
                           'eligible': TheCHWReport.total_muac_eligible()})

    info['registrations'] = Patient.registrations_by_date()

    report_sets = report_framework.report_sets()
    info.update({'report_sets': report_sets})
    return render_to_response(request, template_name, info)


def site_summary(request, report='site', format='json'):
    if request.is_ajax() and format == 'json':
        rpt = None
        if report == 'site':
            #Summary Report
            rpt = SummaryReport.summary()
        elif report == 'general_summary':
            #General Summary report -  all
            rpt = GeneralSummaryReport.summary()
        elif report == 'month':
            #This month summary report
            rpt = MonthSummaryReport.summary()
        elif report == 'week':
            #This Week Summary Report
            rpt = WeekSummaryReport.summary()
        else:
            print report
            return HttpResponse(status=400)
        if format == 'json':
            mimetype = 'application/javascript'
        data = simplejson.dumps(rpt)
        return HttpResponse(data, mimetype)
    # If you want to prevent non XHR calls
    else:
        return HttpResponse(status=400)


class CHWForm(forms.Form):
    #username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField()
    language = forms.CharField(min_length=2, max_length=5)
    location = forms.ChoiceField(choices=[(location.id, location.name) \
                                       for location in Location.objects.all()])
    mobile = forms.CharField(required=False)

@login_required
def add_chw(request):

    if not (request.user.is_staff + request.user.is_superuser):
        redirect(list_chw)

    info = {}

    if request.method == 'POST':
        form = CHWForm(request.POST)
        if form.is_valid():

            #username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password']
            language = form.cleaned_data['language']
            location = form.cleaned_data['location']
            mobile = form.cleaned_data['mobile']

            # CHW creation
            chw = CHW()
            # names and alias
            surname, firstnames, alias = clean_names(u"%s %s" % \
                                  (last_name, first_name), surname_first=True)
            orig_alias = alias[:20]
            alias = orig_alias.lower()
            if alias != chw.alias and not re.match(r'%s\d' % alias, chw.alias):
                n = 1
                while User.objects.filter(username__iexact=alias).count():
                    alias = "%s%d" % (orig_alias.lower(), n)
                    n += 1
                chw.alias = alias
            chw.first_name = firstnames
            chw.last_name = surname
            # properties
            chw.language = language
            chw.location = Location.objects.get(id=location)
            chw.mobile = mobile
            chw.save()

            # set password through User.s
            chw.set_password(password)
            chw.save()

            # Add CHW Group
            chw.groups.add(Group.objects.get(name__iexact='CHW'))

            # create dataentry connection
            c = PersistantConnection(backend=PersistantBackend.objects.get(\
                                                   slug__iexact='debackend'), \
                                     identity=chw.username, \
                                     reporter=chw, \
                                     last_seen=datetime.now())
            c.save()

            # add mobile connection
            try:
                pygsm = PersistantBackend.objects.get(slug__iexact='pygsm')
            except:
                pygsm = PersistantBackend(slug='pygsm', title='pygsm')
                pygsm.save()

            if mobile:
                c = PersistantConnection(backend=pygsm, \
                                         identity=mobile, \
                                         reporter=chw, \
                                         last_seen=datetime.now())
                c.save()

            return HttpResponseRedirect(reverse('childcount.views.index'))
    else:
        form = CHWForm()

    info.update({'form': form})

    return render_to_response(request, 'childcount/add_chw.html', info)

def list_chw(request):

    CHWS_PER_PAGE = 50
    info = {}
    chews = CHW.objects.all().order_by('first_name')
    info.update({'chews': chews})
    paginator = Paginator(chews, CHWS_PER_PAGE)
    page = int(request.GET.get('page', 1))
    info.update({'paginator':paginator.page(page)})

    return render_to_response(request, 'childcount/list_chw.html', info)


def chw(request):
    '''Community Health Worker page '''
    report_title = CHW._meta.verbose_name
    rows = []
    columns, sub_columns = TheCHWReport.chw_bednet_summary()

    reports = TheCHWReport.objects.all()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]

        rows.append(row)

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    if request.method == 'GET' and 'excel' in request.GET:
        '''response = HttpResponse(mimetype="application/vnd.ms-excel")
        filename = "%s %s.xls" % \
                   (report_title, datetime.now().strftime("%d%m%Y"))
        response['Content-Disposition'] = "attachment; " \
                                          "filename=\"%s\"" % filename
        from findug.utils import create_excel
        response.write(create_excel(context_dict))
        return response'''
        return render_to_response(request, 'childcount/chw.html', context_dict)
    else:
        return render_to_response(request, 'childcount/chw.html', context_dict)


def patient(request):
    '''Patients page '''
    MAX_PAGE_PER_PAGE = 30
    DEFAULT_PAGE = 1


    info = {}
    patients = Patient.objects.all()
    try:
        search = request.GET.get('patient_search','')
    except:
        search = ''
    
    if search:
        patients = patients.filter(Q(first_name__icontains=search) | \
                           Q(last_name__icontains=search) | \
                           Q(health_id__icontains=search))

    paginator = Paginator(patients, MAX_PAGE_PER_PAGE)

    try:
        page = int(request.GET.get('page', DEFAULT_PAGE))
    except:
        page = DEFAULT_PAGE
    
    info['rcount'] = patients.count()
    info['rstart'] = paginator.per_page * page
    info['rend'] = (page + 1 * paginator.per_page) - 1
    
    
    try:
        info['patients'] = paginator.page(page)
    except:
        info['patients'] = paginator.page(paginator.num_pages)

    #get the requested page, if its out of range display last page
    try:
        current_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        current_page = paginator.page(paginator.num_pages)

    nextlink, prevlink = {}, {}

    if paginator.num_pages > 1:
        nextlink['page'] = info['patients'].next_page_number()
        prevlink['page'] = info['patients'].previous_page_number()

        info.update(pagenator(paginator, current_page))

    if search != '':
        info['search'] = search
        nextlink['search'] = search
        prevlink['search'] = search
    
    info['prevlink'] = urlencode(prevlink)
    info['nextlink'] = urlencode(nextlink)

    return render_to_response(\
                request, 'childcount/patient.html', info)


def nutrition_png(request):
    nutdata = TheCHWReport.muac_summary()
    return nutdata


def sms_png(request):
    data = TheCHWReport.sms_per_day()
    return data


def bednet_summary(request):
    '''House Patients page '''
    report_title = Patient._meta.verbose_name
    rows = []
    columns, sub_columns = ThePatient.bednet_summary()

    reports = ThePatient.objects.filter(health_id=F('household__health_id'))
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]

        if i == 100:
            row['complete'] = True
            rows.append(row)
            break
        rows.append(row)

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate}

    return render_to_response(\
                request, 'childcount/bednet.html', context_dict)


def clinic_report(request):
    '''House Patients page '''
    report_title = ClinicReport._meta.verbose_name
    rows = []
    columns, sub_columns = ClinicReport.summary()

    reports = ClinicReport.objects.all()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]

        rows.append(row)

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    return context_dict


def pagenator(getpages, reports):
    LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
    LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
    NUM_PAGES_OUTSIDE_RANGE = 2
    ADJACENT_PAGES = 4

    if(getpages.num_pages > 1):
        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)

        if (getpages.num_pages <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, \
                  getpages.num_pages + 1) if n > 0 and n <= getpages.num_pages]
        elif (reports.number <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [n for n in range(1,\
                         LEADING_PAGE_RANGE_DISPLAYED + 1) \
                         if n > 0 and n <= getpages.num_pages]
            pages_outside_leading_range = [n + getpages.num_pages\
                         for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (reports.number > getpages.num_pages - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [n for n in range(\
            getpages.num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, \
            getpages.num_pages + 1) if n > 0 and n <= getpages.num_pages]
            pages_outside_trailing_range = [n + 1 for n in range(0, \
                                    NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_numbers = [n for n in range(\
                    getpages.num_pages - ADJACENT_PAGES, \
                    getpages.num_pages + ADJACENT_PAGES + 1) \
                    if n > 0 and n <= getpages.num_pages]
            pages_outside_leading_range = [n + getpages.num_pages \
                            for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, \
                            NUM_PAGES_OUTSIDE_RANGE)]

        return {
            "is_paginated": getpages.num_pages > 1,
            "previous": reports.previous_page_number(),
            "has_previous": reports.has_previous(),
            "next": reports.next_page_number(),
            "has_next": reports.has_next(),
            "page": reports.number,
            "pages": getpages.num_pages,
            "page_numbers": page_numbers,
            "last_page": getpages.num_pages,
            "in_leading_range": in_leading_range,
            "in_trailing_range": in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range}

@login_required
def edit_patient(request, healthid):
    if healthid is None:
        # Patient to edit was submitted 
        if 'hid' in request.GET:
            return HttpResponseRedirect( \
                "/childcount/patients/edit/%s/" % \
                    (request.GET['hid'].upper()))
        # Need to show patient select form
        else:
            return render_to_response(request,
                'childcount/edit_patient.html', {})
    else: 
        # Handle invalid health IDs
        try:
            patient = Patient.objects.get(health_id=healthid)
        except Patient.DoesNotExist:
            return render_to_response(request,
                'childcount/edit_patient.html', { \
                'health_id': healthid.upper(),
                'failed': True})

        # Save POSTed data
        if request.method == 'POST':
            form = PatientForm(request.POST, instance=patient)
            if form.is_valid():
                print 'saving'
                print form.save(commit=True)
                print patient.household
                return render_to_response(request,
                    'childcount/edit_patient.html', { \
                    'health_id': healthid.upper(),
                    'patient': patient,
                    'success': True})
        # Show patient edit form (nothing saved yet)
        else:
            form = PatientForm(instance=patient)
        return render_to_response(request, 
            'childcount/edit_patient.html', { \
            'form': form,
            'patient': patient,
            'health_id': patient.health_id.upper()
        })
'''
@login_required
def autocomplete(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s|%s\n' % (r.health_id.upper(), r.id)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    patients = Patient.objects.filter(health_id__startswith=q)[:limit]
    return HttpResponse(iter_results(patients), mimetype='text/plain')
'''


