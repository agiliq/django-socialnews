import bforms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from helpers import *
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings as settin
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
import exceptions
from django.core.urlresolvers import reverse
import helpers
from django.core.mail import send_mail
from django.template.loader import render_to_string

def create_user(request):
    if request.method == 'POST':
        form = bforms.UserCreationForm(request.POST)
        loginform = bforms.LoginForm()
        if form.is_valid():
            form.save()
            from django.contrib.auth import authenticate, login
            user = authenticate(username = form.cleaned_data['username'], password = form.cleaned_data['password1'])
            login(request, user)
            return HttpResponseRedirect('/')
    if request.method == 'GET':
        form = bforms.UserCreationForm()
        loginform = bforms.LoginForm()
    payload = {'form':form, 'loginform':loginform}
    return render(request, payload, 'registration/create_user.html', )


def login(request):
    """Login a user.
    Actions avialable:
    Login: Anyone"""
    """Display and processs the login form."""
    no_cookies = False
    account_disabled = False
    invalid_login = False
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settin.LOGIN_REDIRECT_URL
    
    if request.method == 'POST':
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
            form = bforms.LoginForm(request.POST)
            if form.is_valid():
                user = auth.authenticate(username = form.cleaned_data['username'],
                                         password = form.cleaned_data['password'])
                if user:
                    if user.is_active:
                        request.session[settin.PERSISTENT_SESSION_KEY] = form.cleaned_data['remember_user']
                        
                        auth.login(request, user)
                        # login successful, redirect
                        return HttpResponseRedirect(redirect_to)
                    else:
                        account_disabled = True
                else:
                    invalid_login = True
        else:
            no_cookies = True
            form = None
    else:
        form = bforms.LoginForm()
    
    # cookie must be successfully set/retrieved for the form to be processed    
    request.session.set_test_cookie()
    payload = { 'no_cookies': no_cookies,
                                'account_disabled': account_disabled,
                                'invalid_login': invalid_login,
                                'form': form,
                                REDIRECT_FIELD_NAME: redirect_to }
    return render_to_response('registration/login.html', 
                              payload,
                              context_instance = RequestContext(request))


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
        mail_text = render_to_string('registration/password_reset_done.txt', dict(user=user, password=password))
        send_mail('Password reset', mail_text, 'hello@42topics.com', [user.email])
        key.delete()
        payload = {}
        return render(request, payload, 'registration/reset_password_done.html')
    else:
        return HttpResponseForbidden('The key you provided was wrong. Your password could not be reset.')
        
        
        


