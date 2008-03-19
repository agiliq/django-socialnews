from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
import helpers
"""
from django"""

def topic_main(request, topic_name):
    topic = helpers.get_topic(request, topic_name)
    links = topic.link_set.all()

@login_required    
def create(request):
    
    
    