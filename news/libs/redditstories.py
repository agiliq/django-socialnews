#!/usr/bin/python
# 
# Peteris Krumins (peter@catonmat.net)
# http://www.catonmat.net  --  good coders code, great reuse
#
# Released under GNU GPL
#
# Developed as a part of redditriver.com project
# Read how it was designed:
# http://www.catonmat.net/blog/designing-redditriver-dot-com-website
#

import re
import sys
import time
import socket
import urllib2
import datetime
from BeautifulSoup import BeautifulSoup

version = "1.0"

reddit_url = 'http://reddit.com'
subreddit_url = 'http://reddit.com/r'

socket.setdefaulttimeout(30)

class RedesignError(Exception):
    """ An exception class thrown when it seems that Reddit has redesigned """
    pass

class StoryError(Exception):
    """ An exception class thrown when something serious happened """
    pass

def get_stories(subreddit="front_page", pages=1, new=False):
    """ If subreddit front_page, goes to http://reddit.com, otherwise goes to
    http://reddit.com/r/subreddit. Finds all stories accross 'pages' pages
    and returns a list of dictionaries of stories.

    If new is True, gets new stories at http://reddit.com/new or
    http://reddit.com/r/subreddit/new""" 

    stories = [] 
    if subreddit == "front_page":
        url = reddit_url
    else:
        url = subreddit_url + '/' + subreddit
    if new: url += '/new'
    position = 1
    for i in range(pages):
        content = _get_page(url)
        entries = _extract_stories(content)
        stories.extend(entries)
        for story in stories:
            story['url'] = story['url'].replace('&amp;', '&')
            story['position'] = position
            story['subreddit'] = subreddit
            position += 1
        url = _get_next_page(content)
        if not url:
            break

    return stories;

def _extract_stories(content):
    """Given an HTML page, extracts all the stories and returns a list of dicts of them.
    
    See the 'html.examples/story.entry.txt' for an example how HTML of an entry looks like"""

    stories = []
    soup = BeautifulSoup(content)
    entries = soup.findAll('div', id=re.compile('entry_.*'))
    for entry in entries:
        div_title = entry.find('div', id=re.compile('titlerow_.*'));
        if not div_title:
            raise RedesignError, "titlerow div was not found"

        div_little = entry.find('div', attrs={'class': 'little'});
        if not div_little:
            raise RedesignError, "little div was not found"

        title_a = div_title.find('a', id=re.compile('title_.*'))
        if not title_a:
            raise RedesignError, "title a was not found"

        m = re.search(r'title_t\d_(.+)', title_a['id'])
        if not m:
            raise RedesignError, "title did not contain a reddit id"

        id = m.group(1)
        title = title_a.string.strip()
        url = title_a['href']
        if url.startswith('/'): # link to reddit itself
            url = 'http://reddit.com' + url

        score_span = div_little.find('span', id=re.compile('score_.*'))
        if score_span:
            m = re.search(r'(\d+) point', score_span.string)
            if not m:
                raise RedesignError, "unable to extract score"
            score = int(m.group(1))
        else: # for just posted links
            score = 0 # TODO: when this is merged into module, use redditscore to get the actual score
       
        user_a = div_little.find(lambda tag: tag.name == 'a' and tag['href'].startswith('/user/'))
        if not user_a:
            user = '(deleted)'
        else:
            m = re.search('/user/(.+)/', user_a['href'])
            if not m:
                raise RedesignError, "user 'a' tag did not contain href in format /user/(.+)/"

            user = m.group(1)

        posted_re = re.compile("posted(?:&nbsp;|\s)+(.+)(?:&nbsp;|\s)+ago") # funny nbsps
        posted_text = div_little.find(text = posted_re)
        if not posted_text:
            raise RedesignError, "posted ago text was not found"

        m = posted_re.search(posted_text);
        posted_ago = m.group(1)
        unix_time = _ago_to_unix(posted_ago)
        if not unix_time:
            raise RedesignError, "unable to extract story date"
        human_time = time.ctime(unix_time)

        comment_a = div_little.find(lambda tag: tag.name == 'a' and tag['href'].endswith('/comments/'))
        if not comment_a:
            raise RedesignError, "no comment 'a' tag was found"

        if comment_a.string == "comment":
            comments = 0
        else:
            m = re.search(r'(\d+) comment', comment_a.string)
            if not m:
                raise RedesignError, "comment could could not be extracted"
            comments = int(m.group(1))

        stories.append({
            'id': id.encode('utf8'),
            'title': title.encode('utf8'),
            'url': url.encode('utf8'),
            'score': score,
            'comments': comments,
            'user': user.encode('utf8'),
            'unix_time': unix_time,
            'human_time': human_time.encode('utf8')})

    return stories

def _ago_to_unix(ago):
    m = re.search(r'(\d+) (\w+)', ago, re.IGNORECASE)
    if not m:
        return 0

    delta = int(m.group(1))
    units = m.group(2)

    if not units.endswith('s'): # singular
        units += 's' # append 's' to make it plural

    if units == "months":
        units = "days"
        delta *= 30        # lets take 30 days in a month
    elif units == "years":
        units = "days"
        delta *= 365

    dt = datetime.datetime.now() - datetime.timedelta(**{units: delta})
    return int(time.mktime(dt.timetuple()))

def _get_page(url):
    """ Gets and returns a web page at url """

    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')

    try:
        response = urllib2.urlopen(request)
        content = response.read()
    except (urllib2.HTTPError, urllib2.URLError, socket.error, socket.sslerror), e:
        raise StoryError, e

    return content

def _get_next_page(content):
    soup = BeautifulSoup(content)
    a = soup.find(lambda tag: tag.name == 'a' and tag.string == 'next')
    if a:
        return reddit_url + a['href']

def print_stories_paragraph(stories):
    """ Given a list of dictionaries of stories, prints them out paragraph at a time. """
    
    for story in stories:
        print 'position:', story['position']
        print 'subreddit:', story['subreddit']
        print 'id:', story['id']
        print 'title:', story['title']
        print 'url:', story['url']
        print 'score:', story['score']
        print 'comments:', story['comments']
        print 'user:', story['user']
        print 'unix_time:', story['unix_time']
        print 'human_time:', story['human_time']
        print

def print_stories_json(stories):
    """ Given a list of dictionaries of stories, prints them out in json format."""

    import simplejson
    print simplejson.dumps(stories, indent=4)

if __name__ == '__main__':
    from optparse import OptionParser

    description = "A program by Peteris Krumins (http://www.catonmat.net)"
    usage = "%prog [options]"

    parser = OptionParser(description=description, usage=usage)
    parser.add_option("-o", action="store", dest="output", default="paragraph",
                      help="Output format: paragraph or json. Default: paragraph.")
    parser.add_option("-p", action="store", type="int", dest="pages",
                      default=1, help="How many pages of stories to output. Default: 1.")
    parser.add_option("-s", action="store", dest="subreddit", default="front_page",
                      help="Subreddit to retrieve stories from. Default: front_page.")
    parser.add_option("-n", action="store_true", dest="new", 
                      help="Retrieve new stories. Default: nope.")
    options, args = parser.parse_args()

    output_printers = { 'paragraph': print_stories_paragraph,
                        'json': print_stories_json }

    if options.output not in output_printers:
        print >>sys.stderr, "Valid -o parameter values are: paragraph or json!"
        sys.exit(1)

    try:
        stories = get_stories(options.subreddit, options.pages, options.new)
    except RedesignError, e:
        print >>sys.stderr, "Reddit has redesigned! %s!" % e
        sys.exit(1)
    except StoryError, e:
        print >>sys.stderr, "Serious error: %s!" % e
        sys.exit(1)

    output_printers[options.output](stories)

