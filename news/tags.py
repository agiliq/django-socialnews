from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging

def topic_tag(request, topic_slug, tag_text):
    topic = get_topic(request, topic_slug)
    try:
        tag = Tag.objects.get(topic = topic, text = tag_text)
    except Tag.DoesNotExist, e:
        raise Http404
    if request.user.is_authenticated():
        linktags = LinkTag.objects.get_query_set_with_user(user = request.user).filter(tag = tag)
    else:
        linktags = LinkTag.objects.filter(tag = tag).select_related(depth = 1)
    linktags, page_data = get_paged_objects(linktags, request, defaults.LINKS_PER_PAGE)
    payload = dict(topic=topic, tag=tag, linktags=linktags, page_data=page_data)
    return render(request, payload, 'news/tag.html')

def sitewide_tag(request, tag_text):
    try:
        tag = Tag.objects.get(topic__isnull = True, text = tag_text)
    except Tag.DoesNotExist, e:
        raise Http404
    if request.user.is_authenticated():
        linktags = LinkTag.objects.get_query_set_with_user(user = request.user).filter(tag = tag)
    else:
        linktags = LinkTag.objects.filter(tag = tag)
    payload = dict(tag=tag, linktags=linktags)
    return render(request, payload, 'news/tag.html')