#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
Views for logger_ng
'''

import re

from django.core import serializers
from django.http import HttpResponse
from django.utils import simplejson
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required, permission_required
from rapidsms.webui.utils import render_to_response

from logger_ng.models import LoggedMessage
from logger_ng.utils import respond_to_msg


@login_required
@permission_required('logger_ng.can_view')
def index(request):
    '''
    Index view
    '''
    MESSAGES_PER_PAGE = 30

    # If it is a POST then they are responding to a message.
    # Don't allow sending if the user doesn't have the can_respond permission
    if request.method == 'POST' and\
       request.user.has_perm('logger_ng.can_respond'):
       
        for field, value in request.POST.iteritems():
            match = re.match(r'^respond_(?P<id>\d+)$', field)
            if match and len(value) > 1:
                pk = match.groupdict()['id']
                msg = get_object_or_404(LoggedMessage, pk=pk)
                respond_to_msg(msg, value)

        return redirect(index)
    
    # Don't exclude outgoing messages that are a response to another,
    # because they will be shown threaded beneath the original message
    msgs = LoggedMessage.objects.exclude(
                                    direction=LoggedMessage.DIRECTION_OUTGOING,
                                    response_to__isnull=False)
                                    
    # filter from form        
    if request.method == 'GET':
        search = request.GET.get('logger_ng_search_box', '')
        msgs = msgs.filter(Q(identity__icontains=search) | \
                           Q(text__icontains=search) | \
                           Q(reporter__first_name__icontains=search) | \
                           Q(reporter__last_name__icontains=search))

    msgs = msgs.order_by('-date', 'direction')

    paginator = Paginator(msgs, MESSAGES_PER_PAGE)

    # Set the pagination page. Go to page 1 in the event there is no page
    # get variable or if it's something other than a number.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # Try to set the paginator object to the correct page. Set it to the
    # last page if there is some problem with it (too high, etc...)
    
    try:
        msgs = paginator.page(page)
    except (EmptyPage, InvalidPage):
        msgs = paginator.page(paginator.num_pages)

    ctx = locals()
    ctx['request'] = request
    return render_to_response(request, "logger_ng/index.html", ctx)


@permission_required('logger_ng.can_view')
def post_message(request):
    if request.method == 'POST' and \
       request.user.has_perm('logger_ng.can_respond'):
        pk = int(request.POST['id'])
        msg = get_object_or_404(LoggedMessage, pk=pk)
        value = request.POST['msg']
        respond_to_msg(msg, value)
        return HttpResponse('{"status":"none"}', mimetype="text/json")


def latest_messages(request, recent_id):
    """ returns a json list with the messages received since recent_id from passed id parameter """

    try:
        since_message_id = int(recent_id)
    except:
        return HttpResponse("[]")

    try:
        messages = LoggedMessage.objects.filter(id__gt=since_message_id, \
                           direction=LoggedMessage.DIRECTION_INCOMING)[:5]
    except:
        messages = []
    
    msgs = [message.to_dict() for message in messages]
    
    return HttpResponse(simplejson.dumps(msgs), mimetype="text/json")
