#These scripts should be run by cron.
from models import *
import re
from urllib2 import urlparse
import pickle
from datetime import datetime
import os
import logging

sample_corpus_location = defaults.sample_corpus_location
calculate_recommended_timediff = defaults.calculate_recommended_timediff#12 hours
min_links_submitted = defaults.min_links_submitted
min_links_liked = defaults.min_links_liked
calculate_corpus_after = 1
max_links_in_corpus = defaults.max_links_in_corpus
log_file = defaults.log_file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=log_file,
                    filemode='a',
                    )

def _merge_prob_dicts(dict1, dict2):
    merged_dict = {}
    for k,v in dict1.items():
        if k in dict2:
            merged_dict[k] = v + dict2[k]
        else:
            merged_dict[k] = v
    for k, v in dict2.items():
        if k in dict1:
            pass
        else:
            merged_dict[k] = v
    return merged_dict

def _calculate_word_prob_all():
    links = Link.objects.all().order_by('-created_on')[:max_links_in_corpus]
    try:
        corpus = file(sample_corpus_location, 'r')
        corpus_created = os.path.getmtime(sample_corpus_location)
        diff = datetime.now() - datetime.fromtimestamp(corpus_created)
        if diff.days > calculate_corpus_after:
            raise IOError
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
    from django.db import connection
    crsr = connection.cursor()
    
    _prime_linksearch_tbl()
    
    users_sql = """
    SELECT username
    FROM auth_user, news_userprofile
    WHERE
    ((select count(*) from news_link where news_link.user_id = auth_user.id) > %s
    OR (select count(*) from news_linkvote where news_linkvote.user_id = auth_user.id AND news_linkvote.direction = 1) > %s)
    AND auth_user.id = news_userprofile.user_id
    AND (now() - news_userprofile.recommended_calc) > %s
    """ % (min_links_submitted, min_links_liked, calculate_recommended_timediff)
    crsr.execute(users_sql)
    users = crsr.fetchall()
    
    for user in users:
        user = user[0]
        try:
            populate_recommended_link(user)
        except:
            raise
    user_update_sql = """
    UPDATE news_userprofile
    SET recommended_calc = now()            
    """
    crsr.execute(user_update_sql)
    
    links_update_sql = """
    UPDATE news_link
    SET recommended_done = 1
    WHERE recommended_done = 0
    """
    crsr.execute(links_update_sql)
    crsr.close()
    
def calculate_recommendeds_first():
    "Calculate recommended links for new users, who never had a recommended calculation done."
    from django.db import connection
    crsr = connection.cursor()
    
    _prime_linksearch_tbl(include_recommended_done = True)
    profiles = UserProfile.objects.filter(is_recommended_calc = False)
    
    for profile in profiles:
        can_calculate_recs = False
        if LinkVote.objects.filter(user = profile.user).count() > 5:
            can_calculate_recs = True
        if Link.objects.filter(user = profile.user).count() > 5:
            can_calculate_recs = True
        if not can_calculate_recs:
            continue
        try:
            populate_recommended_link(profile.user.username)
        except:
            raise
    
        profile.recommended_calc = datetime.now()
        profile.is_recommended_calc = True
        profile.save()
        
def calculate_relateds():
    _prime_linksearch_tbl(include_recommended_done = True)
    links = Link.objects.filter(related_links_calculated = False)
    for link in links:
        try:
            populate_related_link(link.id)
        except:
            raise
        link.related_links_calculated = True
        link.save()
            
def find_keyword_for_user(username):
    user_corpus = _merge_prob_dicts(_calculate_word_prob_submitted(username),  _calculate_word_prob_liked(username))
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
    logging.debug(sql)
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
    AND NOT news_linksearch.id in (SELECT news_linkvote.link_id FROM news_linkvote, auth_user WHERE auth_user.username = '%s' AND news_linkvote.user_id = auth_user.id)
    limit 0, 10
    """ % (" ".join([keyword[0] for keyword in keywords]).replace("'", "*"), username, username)
    try:
        logging.debug(sql)
    except:
        pass
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def populate_related_link(link_id):
    relateds = find_related_for_link_id(link_id)
    ids = ['-1']+[str(related[0]) for related in relateds]
    sql = """
    INSERT INTO news_relatedlink
    SELECT null, %s, id, .5
    FROM news_link
    WHERE id in (%s)
    """ % (link_id, ','.join(ids))
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("set AUTOCOMMIT = 1")
    logging.debug(sql)
    cursor.execute(sql)
    return cursor.fetchall()

def populate_recommended_link(username):
    relateds = find_recommeneded_for_username(username)
    user = User.objects.get(username= username)
    ids = [str(-1)]+[str(related[0]) for related in relateds]
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

def _prime_linksearch_tbl(include_recommended_done = False):
    #Prime news_linksearch
    #To do this
    #Drop, and recreate the previous table.
    #Insert those liks which have not been recommended.
    #Mark those links as recommended
    from django.db import connection
    crsr = connection.cursor()
    
    commit_sql = 'set autocommit = 1'
    
    drop_sql = 'drop table if exists news_linksearch'
    crsr.execute(drop_sql)
    
    create_sql ="""
    create table news_linksearch
    like
    news_link"""
    crsr.execute(create_sql)
    
    alter_sql = """
    alter table news_linksearch
    engine=MyIsam"""
    crsr.execute(alter_sql)
    
    
    if include_recommended_done:
        insert_sql ="""
        insert into news_linksearch
        select * from news_link
        """
    else:
        insert_sql ="""
        insert into news_linksearch
        select * from news_link
        where news_link.recommended_done = 0"""
        
    crsr.execute(insert_sql)
        
    index_sql = """
    create fulltext index recommender
    on news_linksearch(url, text);    
    """
    crsr.execute(index_sql)

    update_sql="""
    update news_link
    set recommended_done = 1"""
    crsr.execute(update_sql)
    #Priming the news_linksearch table done    
    
    

    
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
    
    