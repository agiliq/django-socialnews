from models import *
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
import exceptions
from django.core.paginator import Paginator, InvalidPage
import random


def get_topic(request, topic_slug):
    try:
        topic = Topic.objects.get(slug=topic_slug)
    except Topic.DoesNotExist:
        raise exceptions.NoSuchTopic

    #If this is a private topic, and you are not  a member, go away
    if topic.permissions == 'Private':
        if not request.user.is_authenticated():
            raise exceptions.PrivateTopicNoAccess
        try:
            SubscribedUser.objects.get(user=request.user, topic=topic)
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
    if not payload.has_key('top_topics'):
        top_topics = Topic.objects.all().order_by('-num_links')[:defaults.TOP_TOPICS_ON_MAINPAGE]
        payload['top_topics'] = top_topics
    if not payload.has_key('new_topics'):
        new_topics = Topic.objects.all().order_by('-updated_on')[:defaults.NEW_TOPICS_ON_MAINPAGE]
        payload['new_topics'] = new_topics
    if not payload.has_key('subscriptions'):
        if request.user.is_authenticated():
            subscriptions = SubscribedUser.objects.filter(user = request.user).select_related(depth = 1)
        else:
            subscriptions = SubscribedUser.objects.get_empty_query_set()
        payload['subscriptions'] = subscriptions
    if not request.user.is_authenticated():
        if not request.session.test_cookie_worked():
            request.session.set_test_cookie()
    return render_to_response(template, payload, RequestContext(request))


def get_pagination_data(obj):
    data = {}
    data['has_next_page'] = obj.has_next()
    if obj.has_next():
        data['next_page'] = obj.next_page_number()
    else:
        data['next_page'] = 1
    data['has_prev_page'] = obj.has_previous()
    if obj.has_previous():
        data['prev_page'] = obj.previous_page_number()
    else:
        data['prev_page'] = 1
    data['first_on_page'] = obj.start_index()
    data['last_on_page'] = obj.end_index()
    return data


def get_paged_objects(query_set, request, obj_per_page):
    try:
        page = request.GET['page']
        page = int(page)
    except KeyError, e:
        page = 1
    pagination = Paginator(query_set, obj_per_page)
    page = pagination.page(page)
    page_data = get_pagination_data(page)
    page_data['total'] = pagination.count
    return page.object_list, page_data


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
