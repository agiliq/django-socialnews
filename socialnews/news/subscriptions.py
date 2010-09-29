from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging
from django.utils import simplejson
import exceptions

@login_required
def subscribe(request, topic_name):
    if not request.method == 'POST':
        return HttpResponseForbidden('Only POST allowed')
    topic = get_topic(request, topic_name)
    subs = SubscribedUser.objects.subscribe_user(user = request.user, topic = topic, group='Member')
    if request.REQUEST.has_key('ajax'):
        dom = '<a href="%s" class="unsubscribe">unsubscribe</a>' % topic.unsubscribe_url()
        payload = dict(action='subscribe', topic=topic.name, id=topic.id, dom=dom)
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
    except CanNotUnsubscribe:
        dom ='<em>Ouch. You created this topic. You can not unsubscribe from this.</em>'
        payload = dict(dom=dom)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    if request.REQUEST.has_key('ajax'):
        dom = '<a href="%s" class="subscribe">subscribe</a>' % topic.subscribe_url()
        payload = dict(action='subscribe', topic=topic.name, id=topic.id, dom=dom)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(topic.get_absolute_url())

    

