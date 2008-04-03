import bforms
from django.http import HttpResponseRedirect
from helpers import *
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings as settin
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views

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


