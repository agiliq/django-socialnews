from django.utils import simplejson
import urllib
import StringIO
from models import DiggLinkRecent, Link, Topic
from django.contrib.auth.models import User
import datetime
import os
import pickle
from libs import redditstories
from BeautifulSoup import BeautifulSoup

digg_user_id = 1
digg_topic_id = 1

digg_user = User.objects.get(id = digg_user_id)
digg_topic = Topic.objects.get(id = digg_topic_id)

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
            main_link = Link.objects.create_link(url = link.url, text=link.title, user = digg_user, topic=digg_topic, karma_factor=False)
            main_link.save()
        except Exception, e:
            print 'Exception'
            print e
            pass
        
def indipad_to_main():
    ip_user_name = 'indiguy'
    ip_topic_name = 'india'
    ipx_user = User.objects.get(username = ip_user_name)
    ipx_topic = Topic.objects.get(name = ip_topic_name)
    base = '/home/shabda/webapps/com_42topic/scraped/indiapad'
    files = [os.path.join(base, f) for f in os.listdir(base)]
    for file_name in files:
        stories = pickle.load(file(file_name))
        for story in stories:
            if story[0].startswith('http'):
                try:
                    Link.objects.create_link(url = story[0], text=story[1], user = ipx_user, topic=ipx_topic, karma_factor=False)
                except Exception, e:
                    print e
                    
def get_redditpics():
    get_reddit_stories('picslover', 'pics', 'pics')
    
def get_redditprog():
    get_reddit_stories('codemonkey', 'programming', 'programming')
    
def get_redditfunny():
    get_reddit_stories('chandler', 'humor', 'funny')    
                    
def get_reddit_stories(username, topicname, subreddit):
    user = User.objects.get(username = username)
    topic = Topic.objects.get(name = topicname)
    stories = redditstories.get_stories(subreddit)
    for story in stories:
        if story['url'].startswith('http'):
            try:
                Link.objects.create_link(url = story['url'], text=story['title'], user = user, topic=topic, karma_factor=False)
            except Exception, e:
                print e
        
    
def scrape_news_yc():
    yc_username = 'startupjunkie'
    yc_topicname = 'startups'
    user = User.objects.get(username = yc_username)
    topic = Topic.objects.get(name = yc_topicname)
    page = urllib.urlopen('http://news.ycombinator.com/')
    page_data = page.read()
    soup = BeautifulSoup(page_data)
    tds = soup.findAll('td', attrs={'class':'title'})
    links = [td('a')[0] for td in tds if td('a')]
    stories = [(link['href'], link.contents[0]) for link in links if link['href'].startswith('http')]
    for story in stories:
        try:
            Link.objects.create_link(url = story[0], text=story[1], user = user, topic=topic, karma_factor=False)
        except Exception, e:
            print e
            
def scrape_sphinn():
    sphinn_username = 'seoguru'
    sphinn_topicname = 'seo'
    user = User.objects.get(username = sphinn_username)
    topic = Topic.objects.get(name = sphinn_topicname)
    page = urllib.urlopen('http://sphinn.com/')
    page_data = page.read()
    soup = BeautifulSoup(page_data)
    stories = zip([div.nextSibling.nextSibling['href'] for div in soup.findAll(attrs={'class':'emph'})],[div('a')[0].contents[0] for div in soup.findAll(attrs={'class':'toptitle'})],)
    for story in stories:
        try:
            Link.objects.create_link(url = story[0], text=story[1], user = user, topic=topic, karma_factor=False)
        except Exception, e:
            print e


def scrape_ballhype():
    def scraper(soup):
        return [(link['href'], link.contents[0]) for link in soup.findAll('a', attrs={'class':'external'})]
    scrape_generic('sporty', 'sports', 'http://ballhype.com/', scraper)
    
            
def scrape_generic(username, topic_name, url, scraper):
    import pdb
    pdb.set_trace()
    user = User.objects.get(username = username)
    topic = Topic.objects.get(name = topic_name)
    page = urllib.urlopen(url)
    page_data = page.read()
    soup = BeautifulSoup(page_data)
    stories = scraper(soup)
    for story in stories:
        try:
            Link.objects.create_link(url = story[0], text=story[1], user = user, topic=topic, karma_factor=False)
        except Exception, e:
            print e    
    
        
def scrape_digg():
    get_stories_new()
    digg_to_main()
        
        
def _get_stories_recent(count = 100, offset = 100):            
    url = 'http://services.digg.com/stories/popular?count=%s&offset=%s&appkey=http://example.com/appli&type=json&sort=promote_date-desc' % (count, offset)
    print url
    stories =  urllib.urlopen(url)
    x = stories.read()
    return StringIO.StringIO(x)