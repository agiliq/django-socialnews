from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import logging

def link_submit(request, topic_name):
    topic = get_topic(request, topic_name)
    if request.method == 'GET':
        form = bforms.NewLink(user = request.user, topic = topic)
    if request.method == 'POST':
        form = bforms.NewLink( user = request.user, topic = topic, data = request.POST)
        if form.is_valid():
            link = form.save()
            return HttpResponseRedirect(link.get_absolute_url())
    payload = {'topic':topic,'form':form}
    return render(request, payload, 'news/create_link.html')

def link_details(request, topic_name, link_id):
    topic = get_topic(request, topic_name)
    if request.user.is_authenticated():
        link = Link.objects.get_query_set_with_user(request.user).get(topic = topic, id = link_id)
    else:
        link = Link.objects.get(topic = topic, id = link_id)
    form = bforms.DoComment(user = request.user, link = link)
    tag_form = bforms.AddTag(user = request.user, link = link)
    if request.method == "GET":
        pass    
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponseForbidden('Please login')
        if request.POST.has_key('comment'):
            form = bforms.DoComment(user = request.user, link = link, data=request.POST)
            if form.is_valid():
                comment = form.save()
                return HttpResponseRedirect('.')
        elif request.POST.has_key('taglink'):
            tag_form = bforms.AddTag(user = request.user, link = link, data=request.POST)
            if tag_form.is_valid():
                comment = tag_form.save()
                return HttpResponseRedirect('.')
    payload = {'topic':topic, 'link':link, 'form':form, 'tag_form':tag_form}
    return render(request, payload, 'news/link_details.html')

def upvote_link(request, link_id):
    link = Link.objects.get(id = link_id)
    try:
        link_vote = LinkVote.objects.get(link = link, user = request.user)
        if link_vote.direction:
            link.reset_vote(request.user)
        if not link_vote.direction:
            vote = link.upvote(request.user)
    except LinkVote.DoesNotExist:
        vote = link.upvote(request.user)
    return HttpResponseRedirect(link.get_absolute_url())

def downvote_link(request, link_id):
    link = Link.objects.get(id = link_id)
    try:
        link_vote = LinkVote.objects.get(link = link, user = request.user)
        if not link_vote.direction:
            link.reset_vote(request.user)
        if link_vote.direction:
            vote = link.downvote(request.user)
    except LinkVote.DoesNotExist:
        vote = link.downvote(request.user)
    return HttpResponseRedirect(link.get_absolute_url())    
    
    