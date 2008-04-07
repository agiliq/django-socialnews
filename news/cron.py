#These scripts should be run by cron.
from models import *
import re
from urllib2 import urlparse
import pickle

sample_corpus_location = 'c:/corpus.db'
calculate_recommended_timediff = 60 * 60 * 12#12 hours
min_links_submitted = 5
min_links_liked = 5

def _calculate_word_prob_all():
    links = Link.objects.all()
    try:
        corpus = file(sample_corpus_location, 'r')
        all_corpus = pickle.load(corpus)
        corpus.close()
    except IOError:
        all_corpus = _calculate_word_prob(links)
        corpus = file(sample_corpus_location, 'w')
        pickle.dump(all_corpus, corpus)
        corpus.close()
    return all_corpus

def _calculate_word_prob_submitted(username):
    links = Link.objects.filter(user__username = username)
    return _calculate_word_prob(links)

def _calculate_word_prob_liked(username):
    votes = LinkVote.objects.filter(user__username = username, direction = True).select_related()
    links = [vote.link for vote in votes]
    return _calculate_word_prob(links)
    
    
def _calculate_word_prob(queryset):
    links = queryset
    corpus = " ".join([_convert_to_text(link) for link in links])
    counts = {}
    corpus_tokens = corpus.split()#re.split(r'[./ ]', corpus)
    for token in corpus_tokens:
        if counts.has_key(token):
            counts[token] += 1
        else:
            counts[token] = 1
    return counts

def _calculate_word_prob_link(link):
    corpus = _convert_to_text(link)
    counts = {}
    corpus_tokens = corpus.split()#re.split(r'[./ ]', corpus)
    for token in corpus_tokens:
        if counts.has_key(token):
            counts[token] += 1
        else:
            counts[token] = 1
    return counts

def _find_improbable_words(user_corpus, sample_corpus):
    avg = 0
    sum = 0
    for k, v in sample_corpus.items():
        sum += v
    avg = float(sum)/len(sample_corpus)
    probs = []
    for k, v in user_corpus.items():
        prob = user_corpus[k]/float(sample_corpus.get(k, avg))
        probs.append((k, prob))
    probs.sort(_compare)
    return probs

def calculate_recommendeds():
    users_sql = """
    SELECT username
    FROM auth_user, news_userprofile
    WHERE
    ((select count(*) from news_link where news_link.user_id = auth_user.id) > %s
    OR (select count(*) from news_linkvote where news_linkvote.user_id = auth_user.id AND news_linkvote.direction = 1) > %s)
    AND auth_user.id = news_userprofile.user_id
    AND (now() - news_userprofile.recommended_calc) > %s
    """ % (min_links_submitted, min_links_liked, calculate_recommended_timediff)
    users_sql1 = """
    SELECT username FROM auth_user, news_userprofile
    WHERE auth_user.id = news_userprofile.user_id
    AND (now() - news_userprofile.recommended_calc) > %s
    """ % calculate_recommended_timediff
    from django.db import connection
    crsr = connection.cursor()
    crsr.execute(users_sql)
    users = crsr.fetchall()
    for user in users:
        user = user[0]
        try:
            populate_recommended_link(user)
        except:
            pass
        
def calculate_relateds():
    links = Link.objects.filter(related_links_calculated = False)
    for link in links:
        link.related_links_calculated = True
        link.save()
        try:
            populate_related_link(link.id)
        except:
            raise
            
def find_keyword_for_user(username):
    user_corpus = _calculate_word_prob_submitted(username) #+ _calculate_word_prob_liked(username)
    words = _find_improbable_words(user_corpus, sample_corpus)
    return words[:len(words)/2]

def find_keywords_for_link(link):
    link_corpus = _calculate_word_prob_link(link)
    words = _find_improbable_words(link_corpus, sample_corpus)
    return words[:len(words)/2]

def find_keywords_for_link_id(link_id):
    link = Link.objects.get(id = link_id)
    link_corpus = _calculate_word_prob_link(link)
    words = _find_improbable_words(link_corpus, sample_corpus)
    return words[:len(words)/2]

def find_related_for_link_id(link_id):
    keywords = find_keywords_for_link_id(link_id)
    sql = """
    select id, text from news_linksearch
    where
    match (url, text)
    against ('%s')
    AND not news_linksearch.text = (SELECT text from news_link where id = %s)
    limit 0, 10
    """ % (" ".join([keyword[0] for keyword in keywords]), link_id)
    print sql
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def find_recommeneded_for_username(username):
    keywords = find_keyword_for_user(username)
    sql = u"""
    select id, text from news_linksearch
    where
    match (url, text)
    against ('%s')
    AND NOT news_linksearch.id in (SELECT news_link.id FROM news_link, auth_user WHERE auth_user.username = '%s' AND news_link.user_id = auth_user.id)
    limit 0, 10
    """ % (" ".join([keyword[0] for keyword in keywords]).replace("'", "*"), username)
    try:
        print sql
    except:
        pass
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def populate_related_link(link_id):
    relateds = find_related_for_link_id(link_id)
    ids = [str(related[0]) for related in relateds]
    sql = """
    INSERT INTO news_relatedlink
    SELECT null, %s, id, .5
    FROM news_link
    WHERE id in (%s)
    """ % (link_id, ','.join(ids))
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("set AUTOCOMMIT = 1")
    #cursor.execute(sql)
    return cursor.fetchall()

def populate_recommended_link(username):
    relateds = find_recommeneded_for_username(username)
    user = User.objects.get(username= username)
    ids = [str(related[0]) for related in relateds]
    sql = """
    INSERT INTO news_recommendedlink
    SELECT null, id, %s, .5
    from news_link
    WHERE id in (%s)
    """ % (user.id, ','.join(ids))
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("set AUTOCOMMIT = 1")
    cursor.execute(sql)
    return cursor.fetchall()
    

    
def _compare(a, b):
    if a[1] > b[1]:
        return -1
    else: return 1    

def _convert_to_text(link):
    parsed = urlparse.urlparse(link.url)
    site = parsed[1]
    rest = ' '.join(re.split(r'[/.-_]', parsed[2]))
    data = '%s %s %s user*%s topic:%s %s' % (site, rest, link.text, link.user.username, link.topic.name, link.topic.full_name)
    data = data.replace("'", "*")
    data = data.replace("%", "*")
    return data

sample_corpus = _calculate_word_prob_all()
    
    