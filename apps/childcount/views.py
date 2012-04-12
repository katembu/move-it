#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import re
import json
from datetime import date, timedelta, datetime
import urllib2
from urllib import urlencode

from rapidsms.webui.utils import render_to_response

#from indicator import Indicator
from direct_sms.utils import send_msg

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _, activate, get_language
from django.utils.translation import check_for_language
from django.utils import simplejson
from django.template import Context, loader
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.db.models import F, Q

from reporters.models import PersistantConnection, PersistantBackend
from locations.models import Location

from childcount.fields import PatientForm, CHWForm
from childcount.models import Patient, CHW, Configuration
from childcount.utils import clean_names, servelet

form_config = Configuration.objects.get(key='dataentry_forms').value
cc_forms = re.split(r'\s*,*\s*', form_config)

@login_required
#@permission_required('childcount.add_encounter')
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


print ">>>>>>>>>>%s" % get_language()
@login_required
def index(request):
    '''Dashboard page '''
    info = {'title': _(u"Move-IT Dashboard")}
    print ">>>>>>>>>>>>>>>%s" % get_language()
    print ">>>>>>>>>>>>>>>%s" % check_for_language('ti')
    info['lang'] = get_language()

    dashboard_template_names = ''
    
    info['dashboard_data'] = '' #dashboard_gather_data(dashboard_template_names)
    #info['section_templates'] = ["%s/%s.html" % (DASHBOARD_TEMPLATE_DIRECTORY, ds) for ds in dashboard_template_names]
    
    return render_to_response(request, "moveit/dashboard.html", info)


try:
    oxd_config = {
        'server_port': Configuration.objects.get(key='oxd_host_port').value
    }
except Configuration.DoesNotExist:
    oxd_config = {
        'server_port': 'http://192.168.0.84:8080',
    }

@login_required
@permission_required('childcount.add_chw')
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
            location = form.cleaned_data['assigned'][0]
            mobile = form.cleaned_data['mobile']
            user_group = form.cleaned_data['user_role']
            assigned_loc = form.cleaned_data['assigned']
            manager = form.cleaned_data['manager']

            print " assigned data>>  %s" % assigned_loc
            print "\n Location >> %s " % location

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

            if manager =='':
                manager = chw
            else:
                manager = CHW.objects.get(pk=manager)

            chw.first_name = firstnames
            chw.last_name = surname
            chw.language = 'en'
            chw.manager = manager
            chw.location = Location.objects.get(id=location)
            chw.mobile = mobile
            chw.save()

            # set password through User.s
            chw.set_password('password')
            chw.save()

            #Assigned location
            for loc in assigned_loc:
                chw.assigned_location.add(Location.objects.get(pk=loc))

            # Add CHW Group
            if not user_group:
                chw.groups.add(Group.objects.get(name__iexact='CHW'))
            else:
                chw.groups.add(Group.objects.get(pk=user_group))

            # create dataentry connection
            '''
            c = PersistantConnection(backend=PersistantBackend.objects.get(\
                                                   slug__iexact='debackend'), \
                                     identity=chw.username, \
                                     reporter=chw, \
                                     last_seen=datetime.now())
            c.save()
            '''

            # add mobile connection
            try:
                pygsm = PersistantBackend.objects.get(slug__iexact='pygsm')
            except:
                pygsm = PersistantBackend(slug='pygsm', title='pygsm')
                pygsm.save()

            if mobile:
                m = PersistantConnection(backend=pygsm, \
                                         identity=mobile, \
                                         reporter=chw, \
                                         last_seen=datetime.now())
                m.save()

            zdata = {
                    'name': chw.get_full_name(),
                    'tel': m.identity,
                    'managername': chw.manager.get_full_name(),
                    'managernumber': \
                                chw.manager.connections.all()[0].identity
,
                    'location': chw.location.name,
                    'role': 'chw' }
                    
            data = urlencode(zdata)
            url = oxd_config['server_port']+'/moveit/chwcreate?'+data

            request = urllib2.Request(url)
            urllib2.urlopen(request).read()
            
            print 'URL  >>>> %s ' % url

            return HttpResponseRedirect(reverse('childcount.views.list_chw'))
    else:
        form = CHWForm()

    info.update({'form': form})

    return render_to_response(request, 'moveit/add_chw.html', info)

@login_required
@permission_required('childcount.add_chw')
def list_chw(request):

    CHWS_PER_PAGE = 50
    info = {}
    chews = CHW.objects.all().order_by('first_name')
    info.update({'chews': chews})
    paginator = Paginator(chews, CHWS_PER_PAGE)
    page = int(request.GET.get('page', 1))
    info.update({'paginator':paginator.page(page)})

    return render_to_response(request, 'moveit/list_chw.html', info)



@login_required
def register(request, eventtype):
    '''
    Registered Person  
    Default is BIRTHS
    '''
    MAX_PAGE_PER_PAGE = 30
    DEFAULT_PAGE = 1

    info = {}

    if eventtype == 'birth':
        filter_eventtype = Patient.BIRTH
    elif eventtype == 'death':
        filter_eventtype = Patient.DEATH
    else:
        filter_eventtype = Patient.BIRTH

    patients = Patient.objects.filter(event_type=filter_eventtype)

    try:
        search = request.GET.get('patient_search','')
    except:
        search = ''
    
    if search:
        if len(search.split()) > 1:
            patients = patients.filter(Q(first_name__search=search,\
                               last_name__search=search) | \
                               Q(health_id__search=search))
        else:
            patients = patients.filter(Q(first_name__search=search)|\
                               Q(last_name__search=search)|\
                               Q(health_id__search=search))

    paginator = Paginator(patients, MAX_PAGE_PER_PAGE)

    try:
        page = int(request.GET.get('page', DEFAULT_PAGE))
    except:
        page = DEFAULT_PAGE
    
    info['rcount'] = patients.count()
    info['rstart'] = paginator.per_page * page
    info['rend'] = (page + 1 * paginator.per_page) - 1
    info['eventtype'] = eventtype
    
    
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
                request, 'moveit/patient.html', info)


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
@permission_required('childcount.change_patient')
def register_edit(request, eventid):
    if eventid is None:
        # Patient to edit was submitted 
        if 'hid' in request.GET:
            return HttpResponseRedirect( \
                "/moveit/register/edit/%s/" % \
                    (request.GET['hid'].upper()))
        # Need to show patient select form
        else:
            return render_to_response(request,
                'moveit/edit_patient.html', {})
    else: 
        # Handle invalid health IDs
        try:
            patient = Patient.objects.get(health_id=eventid)
        except Patient.DoesNotExist:
            return render_to_response(request,
                'moveit/edit_patient.html', { \
                'health_id': eventid.upper(),
                'failed': True})

        # Save POSTed data
        if request.method == 'POST':
            form = PatientForm(request.POST, instance=patient)
            if form.is_valid():
                print 'saving'
                print form.save(commit=True)
                return render_to_response(request,
                    'moveit/edit_patient.html', { \
                    'health_id': eventid.upper(),
                    'patient': patient,
                    'success': True})
        # Show patient edit form (nothing saved yet)
        else:
            form = PatientForm(instance=patient)
        return render_to_response(request, 
            'moveit/edit_patient.html', { \
            'form': form,
            'patient': patient,
            'health_id': patient.health_id.upper()
        })


def chw_json(request):
    chws = CHW.objects.all()
    chwlist = []
    for chw in chws:
        chwlist.append({'pk': chw.pk,'name': chw.__unicode__()})

    json_data = json.dumps(chwlist)
    return HttpResponse(json_data, mimetype="application/json")


def status_update(request, eventid):
    backend = PersistantBackend.objects.get(title='pygsm')
    identity = "254750906055"
    print ">>>>>>>>>>>>>>>"
    return HttpResponse("asdfasdf")
    #msg = backend.message('+254750906055', 'Mose Test')
    #backend._router.outgoing(msg)

    #send_msg(backend=backend, identity=identity, text="Hzzxczello !")
    # send the message to all backends
    #for backend in self._router.backends:
    #c = Connection(backend, identity)
    #msg = Message(connection=c, text='Mose Test', date=datetime.now())
    #msg.send()
