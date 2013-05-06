import bforms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from helpers import *
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings as settin
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views
import exceptions
from django.core.urlresolvers import reverse
import helpers
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.views.generic.edit import FormMixin


class FormCreateUser(FormMixin, View):
    form_class = bforms.UserCreationForm
    template_name = 'registration/create_user.html'
    payload = {'form': 'form', 'loginform': 'loginform'}
    success_url = '/'

    def get(self, request, *args, **kwargs):
        form = bforms.UserCreationForm()
        loginform = bforms.LoginForm()
        self.payload['form'] = form
        self.payload['loginform'] = loginform
        return render(self.request, self.payload, 'registration/create_user.html')

    def form_valid(self, form):
        form.save()
        from django.contrib.auth import authenticate
        user = authenticate(username = form.cleaned_data['username'], password = form.cleaned_data['password1'])
        login(request, user)
        return super(FormCreateUser,self).form_valid(form)

create_user = FormCreateUser.as_view()

@login_required
def user_manage(request):
    "Allows a user to manage their account"
    subs = SubscribedUser.objects.filter(user = request.user).select_related()
    passwordchangeform = bforms.PasswordChangeForm(request.user)
    invites = Invite.objects.filter(user = request.user)
    def_topic_form = bforms.SetDefaultForm(request.user)
    if request.method == 'POST':
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
        if request.POST.has_key('setdef'):
            def_topic_form = bforms.SetDefaultForm(request.user, request.POST)
            if def_topic_form.is_valid():
                def_topic_form.save()
                return HttpResponseRedirect('.')
    payload = dict(subs=subs, form=passwordchangeform, invites=invites, def_topic_form=def_topic_form)
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


class ResetPassword(View):
    payload = {'form': 'form'}

    def get(self, request):
        form = bforms.PasswordResetForm()
        self.payload['form'] = form
        return render(request, self.payload, 'registration/reset_password.html')

    def post(self, request):
        form = bforms.PasswordResetForm(request.POST)
        self.payload['form'] = form
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('reset_password_sent'))
        return render(request, self.payload, 'registration/reset_password.html')


reset_password = ResetPassword.as_view


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
