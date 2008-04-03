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
    votes = LinkVote.objects.get_user_data().filter(user = request.user, direction = True)
    return _user_links(request, votes)

@login_required
def disliked_links(request):
    votes = LinkVote.objects.get_user_data().filter(user = request.user, direction = False)
    return _user_links(request, votes)

@login_required
def saved_links(request):
    saved = SavedLink.objects.get_user_data().filter(user = request.user)
    return _user_links(request, saved)
    

def _user_links(request, queryset):
    queryset, page_data = get_paged_objects(queryset, request, defaults.LINKS_PER_PAGE)
    payload = dict(objects = queryset, page_data=page_data)
    return render(request, payload, 'news/mylinks.html')


@login_required
def user_manage(request):
    "Allows a user to manage their account"
    subs = SubscribedUser.objects.filter(user = request.user).select_related()
    passwordchangeform = bforms.PasswordChangeForm(request.user)
    invites = Invite.objects.filter(user = request.user)
    if request.method=='POST':
        if request.POST.has_key('remove'):
            topic_name = request.POST['topic']
            topic = Topic.objects.get(name=topic_name)
            sub = SubscribedUser.objects.get(user = request.user, topic = topic)
            sub.delete()
        if request.POST.has_key('changepassword'):
            passwordchangeform = bforms.PasswordChangeForm(request.user, request.POST)
            if passwordchangeform.is_valid():
                passwordchangeform.save()
                return HttpResponseRedirect('.')
    payload = dict(subs=subs, form=passwordchangeform, invites=invites)
    return render(request, payload, 'news/usermanage.html')

def activate_user(request, username):
    user = User.objects.get(username=username)
    try:
        key = EmailActivationKey.objects.get(user = user)
    except EmailActivationKey.DoesNotExist:
        return HttpResponseForbidden('The activion key was wrong. Your email could not be validated.')
    request_key = request.GET.get('key', '')
    if request_key == key.key:
        profile = user.get_profile()
        profile.email_validated = True
        profile.save()
        key.delete()
        payload = {}
        return render(request, payload, 'registration/email_validated.html')
    else:
        return HttpResponseForbidden('The activation key was wrong. Your email could not be validated.')
    
def reset_password(request):
    if request.method == 'GET':
        form = bforms.PasswordResetForm()
    elif request.method == 'POST':
        form = bforms.PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('reset_password_sent'))
    payload = {'form':form}
    return render(request, payload, 'registration/reset_password.html')

def reset_password_sent(request):
    payload = {}
    return render(request, payload, 'registration/reset_password_sent.html')
            

def reset_password_done(request, username):
    user = User.objects.get(username=username)
    try:
        key = PasswordResetKey.objects.get(user = user)
    except PasswordResetKey.DoesNotExist:
        return HttpResponseForbidden('The key you provided was wrong. Your password could not be reset.')
    request_key = request.GET.get('key', '')
    if request_key == key.key:
        password = helpers.generate_random_key()
        user.set_password(password)
        #helpers.send_mail_test(user = user, message=password)
	mail_text = render_to_string('registration/password_reset_done.txt', dict(user=user, password=password))
	send_mail('Password reset', mail_text, 'hello@42topics.com', [user.email])
        key.delete()
        payload = {}
        return render(request, payload, 'registration/reset_password_done.html')
    else:
        return HttpResponseForbidden('The key you provided was wrong. Your password could not be reset.')
        
        
        