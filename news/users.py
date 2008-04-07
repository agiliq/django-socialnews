from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import exceptions
from django.conf import settings as settin
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
import helpers
from django.core.mail import send_mail
from django.template.loader import render_to_string

def user_main(request, username):
    user = User.objects.get(username = username)
    if request.user.is_authenticated():
        links = Link.objects.get_query_set_with_user(request.user).filter(user = user).select_related()
    else:
        links = Link.objects.filter(user = user).select_related()
    links, page_data = get_paged_objects(links, request, defaults.LINKS_PER_PAGE)
    payload = dict(pageuser=user, links=links, page_data=page_data)
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
def liked_links(request):
    votes = LinkVote.objects.get_user_data().filter(user = request.user, direction = True).select_related()
    return _user_links(request, votes)

@login_required
def disliked_links(request):
    votes = LinkVote.objects.get_user_data().filter(user = request.user, direction = False).select_related()
    return _user_links(request, votes)

@login_required
def saved_links(request):
    saved = SavedLink.objects.get_user_data().filter(user = request.user).select_related()
    return _user_links(request, saved)
    

def _user_links(request, queryset):
    queryset, page_data = get_paged_objects(queryset, request, defaults.LINKS_PER_PAGE)
    payload = dict(objects = queryset, page_data=page_data)
    return render(request, payload, 'news/mylinks.html')

