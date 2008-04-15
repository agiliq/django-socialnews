from django.utils import simplejson
import urllib
import StringIO
from models import DiggLinkRecent, Link, Topic
from django.contrib.auth.models import User
import datetime

digg_user_id = 1
digg_topic_id = 1

user = User.objects.get(id = digg_user_id)
topic = Topic.objects.get(id = digg_topic_id)

def get_stories_new():
    for i in xrange(1):
        stories = simplejson.load(_get_stories_recent(offset = i*100))
        stories = stories['stories']
        for story in stories:
            try:
                link = DiggLinkRecent(url = story['link'], description=story['description'], title=story['title'])
                link.username = story['user']['name']
                link.submitted_on = datetime.datetime.fromtimestamp(story['submit_date'])
                link.save()
            except Exception, e:
                print e
                pass
    
def digg_to_main():
    links = DiggLinkRecent.objects.filter(is_in_main=False)
    for link in links:
        try:
            link.is_in_main = True
            link.save()
            main_link = Link.objects.create_link(url = link.url, text=link.title, user = user, topic=topic, karma_factor=False)
            main_link.save()
        except Exception, e:
            print 'Exception'
            print e
            pass
        
def scrape_digg():
    get_stories_new()
    digg_to_main()
        
        
def _get_stories_recent(count = 100, offset = 100):            
    url = 'http://services.digg.com/stories/popular?count=%s&offset=%s&appkey=http://example.com/appli&type=json&sort=promote_date-desc' % (count, offset)
    print url
    stories =  urllib.urlopen(url)
    x = stories.read()
    return StringIO.StringIO(x)