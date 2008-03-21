from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging
import simplejson

@login_required
def subscribe(request, topic_name):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only POST allowed')
    topic = get_topic(request, topic_name)
    subs = SubscribedUser.objects.subscribe_user(user = request.user, topic = topic, group='Member')
    if request.REQUEST.has_key('ajax'):
        payload = dict(action='subscribe', topic=topic.name, id=topic.id)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(topic.get_absolute_url())

@login_required
def unsubscribe(request, topic_name):
    topic = get_topic(request, topic_name)
    if not request.method == 'POST':
        return HttpResponseForbidden('Only POST allowed')
    try:
        subs = SubscribedUser.objects.get(user = request.user, topic = topic)
        subs.delete()        
    except SubscribedUser.DoesNotExist:
        pass
    if request.REQUEST.has_key('ajax'):
        payload = dict(action='subscribe', topic=topic.name, id=topic.id)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(topic.get_absolute_url())

    

