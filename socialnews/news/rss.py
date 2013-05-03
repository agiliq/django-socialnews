from django.contrib.syndication.views import FeedDoesNotExist, Feed
import models


class LatestEntries(Feed):
    def get_object(self, bits):
        if len(bits) != 0:
            raise models.Topic.DoesNotExist
        return 'LatestFeed'

    title = 'Latest links posted at 42topics.com'

    link = '/'

    description = 'Latest links posted at 42topics.com'

    def items(self, obj):
        return models.Link.objects.all().order_by('-created_on')[:30]


class LatestEntriesByTopic(Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise models.Topic.DoesNotExist
        return models.Topic.objects.get(name__exact=bits[0])

    def title(self, obj):
        return "42Topics.com: Links from topic %s" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.full_name

    def items(self, obj):
        return models.Link.objects.filter(topic = obj).order_by('-created_on')[:30]
