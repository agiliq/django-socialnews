from django import newforms as forms
from django.contrib.auth.models import User
from django.newforms import ValidationError
import defaults
from models import *
import re
from django.utils.translation import ugettext as _
from django.newforms import widgets
from django.contrib.auth.models import User
import helpers
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string

class NewTopic(forms.Form):
    "Create a new topic."
    topic_name = forms.CharField(max_length = 100)
    topic_fullname = forms.CharField(max_length = 100)
    permission = forms.ChoiceField(choices = topic_permissions)
    
    about = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, user, topic_name=None, *args, **kwargs):
        super(NewTopic, self).__init__(*args, **kwargs)
        self.user = user
        if topic_name:
            self.fields['topic_name'].initial = topic_name
    
    def clean_topic_name(self):
        try:
            name = self.cleaned_data['topic_name']
            Topic.objects.get(name = name)
        except Topic.DoesNotExist, e:
            return name
        raise ValidationError('The name %s is already taken. Try something else?' % name)
    
    def clean(self):
        if self.user.get_profile().karma < defaults.KARMA_COST_NEW_TOPIC:
            raise ValidationError('You do not have enogh karma')
        return self.cleaned_data
    
    def save(self):
        return Topic.objects.create_new_topic(user = self.user, full_name=self.cleaned_data['topic_fullname'], topic_name=self.cleaned_data['topic_name'], about = self.cleaned_data['about'], permissions = self.cleaned_data['permission'])
    
    
class NewLink(forms.Form):
    url = forms.URLField()
    text = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, topic, user, *args, **kwargs):
        super(NewLink, self).__init__(*args, **kwargs)
        self.user = user
        self.topic = topic
        
    def clean_url(self):
        try:
            Link.objects.get(topic = self.topic, url = self.cleaned_data['url'])
        except Link.DoesNotExist, e:
            return self.cleaned_data['url']
        raise ValidationError('This link has already been submitted.')
    
    def clean(self):
        if self.user.get_profile().karma < defaults.KARMA_COST_NEW_LINK:
            raise ValidationError('You do not have enogh karma')
        return self.cleaned_data
    
    def save(self):
        return Link.objects.create_link(url = self.cleaned_data['url'], text = self.cleaned_data['text'], user = self.user, topic = self.topic)
    
class DoComment(forms.Form):
    text = forms.CharField(widget = forms.Textarea)
    
    def __init__(self, user, link, *args, **kwargs):
        super(DoComment, self).__init__(*args, **kwargs)
        self.user = user
        self.link = link
        
    def save(self):
        return Comment.objects.create_comment(link = self.link, user = self.user, comment_text = self.cleaned_data['text'])
    
class DoThreadedComment(forms.Form):
    text = forms.CharField(widget = forms.Textarea)
    parent_id = forms.CharField(widget = forms.HiddenInput)
    
    def __init__(self, user, link, parent, *args, **kwargs):
        super(DoThreadedComment, self).__init__( *args, **kwargs)
        self.user = user
        self.link = link
        self.parent = parent
        self.fields['parent_id'].initial = parent.id
    
    def save(self):
        return Comment.objects.create_comment(link = self.link, user = self.user, comment_text = self.cleaned_data['text'], parent = self.parent)
    
class AddTag(forms.Form):
    tag = forms.CharField(max_length = 100)
    
    def __init__(self, user, link, *args, **kwargs):
        super(AddTag, self).__init__(*args, **kwargs)
        self.user = user
        self.link = link
        
    def save(self):
        return LinkTagUser.objects.tag_link(tag_text = self.cleaned_data['tag'], link = self.link, user=self.user)
  
class LoginForm(forms.Form):
    """Login form for users."""
    username = forms.RegexField(r'^[a-zA-Z0-9_]{1,30}$',
                                max_length = 30,
                                min_length = 1,
                                widget = widgets.TextInput(attrs={'class':'input'}),
                                error_message = 'Must be 1-30 alphanumeric characters or underscores.')
    password = forms.CharField(min_length = 1, 
                               max_length = 128, 
                               widget = widgets.PasswordInput(attrs={'class':'input'}),
                               label = 'Password')
    remember_user = forms.BooleanField(required = False, 
                                       label = 'Remember Me')
    
    def clean(self):
        try:
            user = User.objects.get(username__iexact = self.cleaned_data['username'])
        except User.DoesNotExist, KeyError:
            raise forms.ValidationError('Invalid username, please try again.')
        
        if not user.check_password(self.cleaned_data['password']):
            raise forms.ValidationError('Invalid password, please try again.')
        
        return self.cleaned_data
    
class UserCreationForm(forms.Form):
    """A form that creates a user, with no privileges, from the given username and password."""
    username = forms.CharField(max_length = 30, required = True)
    password1 = forms.CharField(max_length = 30, required = True, widget = forms.PasswordInput)
    password2 = forms.CharField(max_length = 30, required = True, widget = forms.PasswordInput)
    email = forms.EmailField(required = False)
    
    def clean_username (self):
        alnum_re = re.compile(r'^\w+$')
        if not alnum_re.search(self.cleaned_data['username']):
            raise ValidationError("This value must contain only letters, numbers and underscores.")
        self.isValidUsername()
        return self.cleaned_data['username']

    def clean (self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise ValidationError(_("The two password fields didn't match."))
        return super(forms.Form, self).clean()
        
    def isValidUsername(self):
        try:
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            return
        raise ValidationError(_('A user with that username already exists.'))
    
    def clean_email(self):
        if not self.cleaned_data['email']:
            return self.cleaned_data['email']
        try:
            User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        #raise ValidationError(_('A user with this email already exists.'))
	pass
    
    def save(self):
        if self.cleaned_data['email']:
            email = self.cleaned_data['email']
        else:
            email = ''
        user = UserProfile.objects.create_user(user_name = self.cleaned_data['username'], email=email, password=self.cleaned_data['password1'])
        if self.cleaned_data['email']:
            #generate random key
            keyfrom = 'abcdefghikjlmnopqrstuvwxyz1234567890'
            key = "".join([random.choice(keyfrom) for i in xrange(50)])
            EmailActivationKey.objects.save_key(user, key)
            #helpers.send_mail_test(user=user, message = key)
	    mail_text = render_to_string('registration/new_user_mail.txt', dict(key=key, user=user))
	    send_mail('Your account was created.', mail_text, 'hello@42topics.com', [user.email])
                
    
class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(max_length = 30, required = True, widget = forms.PasswordInput)
    password1 = forms.CharField(max_length = 30, required = True, widget = forms.PasswordInput)
    password2 = forms.CharField(max_length = 30, required = True, widget = forms.PasswordInput)
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        
    def clean_old_password(self):
        if not self.user.check_password(self.cleaned_data['old_password']):
            raise forms.ValidationError('Invalid password, please try again.')
        return self.cleaned_data['old_password']
    
    def clean(self):
        try:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise ValidationError(_("The two password fields didn't match."))
        except KeyError, e:
            pass
        return super(PasswordChangeForm, self).clean()
    
    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save()
        return self.user
    
class PasswordResetForm(forms.Form):
    email = forms.EmailField()
    
    def clean_email(self):
        try:
            user = User.objects.get(email = self.cleaned_data['email'])
            self.user = user
        except User.DoesNotExist:
            raise ValidationError(_('There is no user with this email.'))
        return self.cleaned_data['email']
    
    def save(self):
        keyfrom = 'abcdefghikjlmnopqrstuvwxyz1234567890'
        key = "".join([random.choice(keyfrom) for i in xrange(50)])
        PasswordResetKey.objects.save_key(user = self.user, key = key)
	mail_text = render_to_string('registration/password_reset_mail.txt', dict(key=key, user=self.user))
        #helpers.send_mail_test(user=self.user, message = key)
	send_mail('Password reset request', mail_text, 'hello@42topics.com', [self.user.email])
        
            
    
class InviteUserForm(forms.Form):
    username = forms.CharField(max_length = 100)
    invite_text = forms.CharField(max_length = 1000, widget = forms.Textarea, required = False)
    
    
    def __init__(self, topic, *args, **kwargs):
        self.topic = topic
        super(InviteUserForm, self).__init__(*args, **kwargs)
        
    def clean_username(self):
        try:
            user = User.objects.get(username = self.cleaned_data['username'])
        except User.DoesNotExist:
            raise ValidationError(_('There is no user with username %s.' % self.cleaned_data['username']))
        try:
            invite = Invite.objects.get(user = user, topic = self.topic)
        except Invite.DoesNotExist:
            pass
        else:
            raise ValidationError(_('User %s has already been invited.' % self.cleaned_data['username']))
        try:
            invite = SubscribedUser.objects.get(user = user, topic = self.topic)
        except SubscribedUser.DoesNotExist:
            pass
        else:
            raise ValidationError(_('User %s is already subscribed to %s.' % (self.cleaned_data['username'], self.topic.name)))
        return self.cleaned_data['username']
    
    
    
    def save(self):
        user = User.objects.get(username = self.cleaned_data['username'])
        invite = Invite.objects.invite_user(user = user, topic = self.topic, text = self.cleaned_data['invite_text'])
        return invite
        
        
        
        
        
        
        
        
        