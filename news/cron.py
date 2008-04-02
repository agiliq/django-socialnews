#These scripts should be run by cron.
from models import *
import re
from urllib2 import urlparse

def _calculate_word_prob_all():
    links = Link.objects.all()
    return _calculate_word_prob(links)

def _calculate_word_prob_submitted(username):
    links = Link.objects.filter(user__username = username)
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

sample_corpus = _calculate_word_prob_all()
    
def find_keyword_for_user(username):
    user_corpus = _calculate_word_prob_submitted(username)
    words = _find_improbable_words(user_corpus, sample_corpus)
    return words[:100]
    
    
def _compare(a, b):
    if a[1] > b[1]:
        return -1
    else: return 1    

def _convert_to_text(link):
    parsed = urlparse.urlparse(link.url)
    site = parsed[1]
    rest = ' '.join(re.split(r'[/.-_]', parsed[2]))
    return '%s %s %s user:%s topic:%s %s' % (site, rest, link.text, link.user.username, link.topic.name, link.topic.full_name)
    
    