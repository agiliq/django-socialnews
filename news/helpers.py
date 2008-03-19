from models import *
from django.http import Http404

def get_topic(request, topic_name):
    try:
        topic = Topic.objects.get(name = topic_name)
    except Topic.DoesNotExist:
        raise Http404
    
    return topic
    