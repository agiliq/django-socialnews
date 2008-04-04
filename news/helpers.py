from models import *
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
import exceptions
from django.core.paginator import ObjectPaginator, InvalidPage
import random

def get_topic(request, topic_name):
    try:
        topic = Topic.objects.get(name = topic_name)
    except Topic.DoesNotExist:
        raise exceptions.NoSuchTopic
    #If this is a private topic, and you are not  a member, go away
    if topic.permissions == 'Private':
        if not request.user.is_authenticated():
            raise exceptions.PrivateTopicNoAccess
        try:
            SubscribedUser.objects.get(user = request.user, topic = topic)
        except SubscribedUser.DoesNotExist:
            raise exceptions.PrivateTopicNoAccess
        
    return topic

def render(request, payload, template):
    "Add sitewide actions"
    if request.user.is_authenticated():
        try:
            topic = payload['topic']
            sub = SubscribedUser.objects.get(topic = topic, user = request.user)
            payload['access'] = sub.group
        except SubscribedUser.DoesNotExist:
            pass
        except KeyError:
            pass
    return render_to_response(template, payload, RequestContext(request))

def get_pagination_data(obj_page, page_num):
    data = {}
    page_num = int(page_num)
    data['has_next_page'] = obj_page.has_next_page(page_num)
    data['next_page'] = page_num + 1
    data['has_prev_page'] = obj_page.has_previous_page(page_num)
    data['prev_page'] = page_num - 1
    data['first_on_page'] = obj_page.first_on_page(page_num)
    data['last_on_page'] = obj_page.last_on_page(page_num)
    data['total'] = obj_page.hits
    return data

def get_paged_objects(query_set, request, obj_per_page):
    try:
        page = request.GET['page']
        page = int(page)
    except KeyError, e:
        page = 0
    object_page = ObjectPaginator(query_set, obj_per_page)
    object = object_page.get_page(page)
    page_data = get_pagination_data(object_page, page)
    return object, page_data
    
def check_permissions(topic, user):
    "Check that the current user has permssions to acces the page or raise exception if no"
    if topic.permissions == 'Private':
        try:
            SubscribedUser.objects.get(user = user, topic = topic)
        except SubscribedUser.DoesNotExist:
            raise exceptions.PrivateTopicNoAccess
        
def generate_random_key(length = None):
    if not length:
        length = random.randint(6, 10)
    keychars = 'abcdefghikjlmnopqrstuvwxyz1234567890'
    key = "".join([random.choice(keychars) for i in xrange(length)])
    return key
    
    
    