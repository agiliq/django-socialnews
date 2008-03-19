from django import newforms as forms
from django.contrib.auth.models import User
from django.newforms import ValidationError
import defaults
from models import *

class NewTopic(forms.Form):
    "Create a new topic."
    topic_name = forms.CharField(max_length = 100)
    
    def __init__(self, user, *args, **kwargs):
        super(NewTopic, self).__init__(*args, **kwargs)
        self.user = user
    
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
        return Topic.objects.create_new_topic(user = self.user, topic_name=self.cleaned_data['topic_name'])
    
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
        #Link.objects.create
        pass
        
        