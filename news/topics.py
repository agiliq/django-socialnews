from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import exceptions


def main(request):
    "Sitewide main page"
    if request.user.is_authenticated():
        subs = SubscribedUser.objects.filter(user = request.user)
        topics = [sub.topic for sub in subs]
        links = Link.objects.filter(topic__in = topics)
    else:
        links = Link.objects.all()
    tags = Tag.objects.filter(topic__isnull = True)
    payload = {'links':links, 'tags':tags}
    return render(request, payload, 'news/main.html')
        
        
    

def topic_main(request, topic_name):
    try:
        topic = get_topic(request, topic_name)
    except exceptions.NoSuchTopic, e:
        return HttpResponseRedirect('/create_topic/?topic_name=%s' % topic_name)
    tags = Tag.objects.filter(topic = topic)
    if request.user.is_authenticated():
        links = Link.objects.get_query_set_with_user(request.user).filter(topic = topic)
    else:
        links = Link.objects.filter(topic = topic)
    subscribed = False
    if request.user.is_authenticated():
        subscriptions = SubscribedUser.objects.select_related(depth=1).filter(user = request.user)
        try:
            SubscribedUser.objects.get(topic = topic, user = request.user)
            subscribed = True
        except SubscribedUser.DoesNotExist:
            pass
    else:
        subscriptions = SubscribedUser.objects.get_empty_query_set()
    
    payload = dict(topic = topic, links = links, subscriptions=subscriptions, tags=tags, subscribed=subscribed)
    return render(request, payload, 'news/topic_main.html')

@login_required    
def create(request, topic_name=None):
    if request.method == 'GET':
        if not topic_name:
            topic_name = request.GET.get('topic_name', '')
            form = bforms.NewTopic(user = request.user, topic_name = topic_name)
        else:
            form = bforms.NewTopic(user = request.user, topic_name = topic_name)
    elif request.method == 'POST':
        form = bforms.NewTopic(user = request.user, data = request.POST)
        if form.is_valid():
            topic = form.save()
            return HttpResponseRedirect(topic.get_absolute_url())
            
    payload = {'form':form}
    return render(request, payload, 'news/create_topic.html')

    
    
    
    