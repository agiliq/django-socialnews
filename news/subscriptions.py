from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging

@login_required
def subscribe(request, topic_name):
    topic = get_topic(request, topic_name)
    subs = SubscribedUser.objects.subscribe_user(user = request.user, topic = topic, group='Memeber')
    return HttpResponseRedirect(topic.get_absolute_url())

@login_required
def unsubscribe(request, topic_name):
    topic = get_topic(request, topic_name)
    try:
        subs = SubscribedUser.objects.get(user = request.user, topic = topic)
        subs.delete()        
    except SubscribedUser.DoesNotExist:
        pass
    return HttpResponseRedirect(topic.get_absolute_url())

    

