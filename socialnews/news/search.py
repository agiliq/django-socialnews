import urllib2, urllib
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
import defaults
from helpers import render


site = defaults.SITE

def search (request):
    if not request.GET.has_key('q'):
       payload = {}
    else:
            query_term = ""
            for term in request.GET['q']:
                query_term += term
            try:
              start = request.GET['start']
            except:
              start = 0
            start = int(start)
            end = int(start) + 10
            results_data = get_search_results('YLPjx2rV34F4hXcTnJYqYJUj9tANeqax76Ip2vADl9kKuByRNHgC4qafbATFoQ', query_term, site = site, start = start)
            
            if start < int(results_data['totalResultsAvailable']) - 1:
               next_page = start + 10
               next_page_url = '/?%s' % urllib.urlencode({'q':query_term, 'start':next_page})
            if start > 0:
               prev_page = max(0, start - 10)
               prev_page_url = '/?%s' % urllib.urlencode({'q':query_term, 'start':prev_page})
            
            
            results = results_data['Result']
    payload = locals()#{'results':results, 'results_data':results_data,'query_term':query_term}
    return render(request, payload, 'news/search.html')

def get_search_results(appid, query, region ='us', type = 'all', results = 10, start = 0, format ='any', adult_ok = "", similar_ok = "", language = "", country = "", site = "", subscription = "", license = ''):
    base_url = u'http://search.yahooapis.com/WebSearchService/V1/webSearch?'
    params = locals()
    result = _query_yahoo(base_url, params)
    return result['ResultSet']

def _query_yahoo(base_url, params):
    params['output'] = 'json'
    payload = urllib.urlencode(params)
    url = base_url + payload
    print url
    response = urllib2.urlopen(url)
    result = simplejson.load(response)
    return result    
