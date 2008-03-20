from models import *
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
import exceptions

def get_topic(request, topic_name):
    try:
        topic = Topic.objects.get(name = topic_name)
    except Topic.DoesNotExist:
        raise exceptions.NoSuchTopic
    return topic

def render(request, payload, template):
    return render_to_response(template, payload, RequestContext(request))
    
    