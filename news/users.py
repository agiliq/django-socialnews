from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import exceptions
from django.conf import settings as settin
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME

def user_main(request, username):
    user = User.objects.get(username = username)
    if request.user.is_authenticated():
        links = Link.objects.get_query_set_with_user(request.user).filter(user = user).select_related()
    else:
        links = Link.objects.filter(user = user).select_related()
    payload = dict(pageuser=user, links=links)
    return render(request, payload, 'news/userlinks.html')

def user_comments(request, username):
    user = User.objects.get(username = username)
    if request.user.is_authenticated():
        comments = Comment.objects.get_query_set_with_user(request.user).filter(user = user).select_related()
    else:
        comments = Comment.objects.filter(user = user).select_related()
    payload = dict(pageuser=user, comments=comments)
    return render(request, payload, 'news/usercomments.html')    

@login_required
def user_manage(request):
    "Allows a user to manage their account"
    subs = SubscribedUser.objects.filter(user = request.user).select_related()
    if request.method=='POST':
        if request.POST.has_key('remove'):
            topic_name = request.POST['topic']
            topic = Topic.objects.get(name=topic_name)
            sub = SubscribedUser.objects.get(user = request.user, topic = topic)
            sub.delete()
    payload = dict(subs=subs)
    return render(request, payload, 'news/usermanage.html')