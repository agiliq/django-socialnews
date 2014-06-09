from django.conf import settings
from django.conf.urls import url, patterns, include
from django.contrib import admin
from django.contrib.auth import views
from django.views.generic.base import TemplateView

from news.rss import LatestEntriesByTopic, LatestEntries

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^implist/', include('implist.foo.urls')),

    url(r'^google42f6e952fe543f39.html$', TemplateView.as_view(template_name = 'news/test.txt')),
    url(r'^robots.txt$', TemplateView.as_view(template_name = 'news/robots.txt')),
    url(r'^foo/$', TemplateView.as_view(template_name ='news/base.html')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^logout/$', views.logout, {'template_name':'registration/logout.html'}, name='logout'),
)

urlpatterns += patterns('news.accounts',
    url(r'^register/$', 'create_user', name='register'),
    url(r'^user/reset_password/$', 'reset_password', name='reset_password'),
    url(r'^user/reset_password/sent/$', 'reset_password_sent', name='reset_password_sent'),
    url(r'^user/reset_password/done/(?P<username>[^\.^/]+)/$', 'reset_password_done', name='reset_password_done'),
    url(r'^user/activate/(?P<username>[^\.^/]+)/$', 'activate_user', name='activate_user'),
    url(r'^my/$', 'user_manage', name='user_manage'),
)


urlpatterns += patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'registration/login.html'}, name = 'login'),)


urlpatterns += patterns('',
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^dummy/', TemplateView.as_view(template_name='news/dummy.html'))
)

urlpatterns += patterns('news.subscriptions',
    url(r'^subscribe/(?P<topic_slug>[\w-]+)/$', 'subscribe', name='subscribe'),
    url(r'^unsubscribe/(?P<topic_slug>[\w-]+)/$', 'unsubscribe', name='unsubscribe'),
)

urlpatterns += patterns('news.search',
    url(r'^search/$', 'search', name='search'),
)

urlpatterns +=patterns('news.users',
    url(r'^user/(?P<username>[^\.^/]+)/$', 'user_main', name='user_main'),
    url(r'^user/(?P<username>[^\.^/]+)/comments/$', 'user_comments', name='user_comments'),
    url(r'^user/likedlinks/(?P<username>[^\.^/]+)/(?P<secret_key>[^\.^/]+)/$', 'liked_links_secret', name='liked_links_secret'),
    url(r'^my/liked/$', 'liked_links', name='liked_links'),
    url(r'^my/disliked/$', 'disliked_links', name='disliked_links'),
    url(r'^my/saved/$', 'saved_links', name='saved_links'),
)

urlpatterns += patterns('news.static',
    url(r'^aboutus/$', 'aboutus', name='aboutus'),
    url(r'^help/$', 'help', name='help'),
    url(r'^help/$', 'help', name='help'),
    url(r'^buttons/$', 'buttons', name='buttons'),
)

urlpatterns += patterns('news.tags',
    url(r'^(?P<topic_slug>[\w-]+)/tag/(?P<tag_text>[^\.^/]+)/$', 'topic_tag', name='topic_tag'),
    url(r'^tag/(?P<tag_text>[^\.^/]+)/$', 'sitewide_tag', name='sitewide_tag'),
)

feeds = {
    'latest': LatestEntries,
    'topics': LatestEntriesByTopic,
}

urlpatterns += patterns('',
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.Feed', {'feed_dict': feeds}),
)

urlpatterns += patterns('news.topics',
    url(r'^$', 'main', name='main'),
    url(r'^new/$', 'main', {'order_by':'new'}, name='new'),
    url(r'^all/$', 'main', {'order_by':'new', 'override':'all'}, name='new'),
    url(r'^recommended/$', 'recommended',  name='recommended'),
    url(r'^createtopic/', 'create', name='createtopic'),
    url(r'^about/$', 'site_about', name='site_about'),
    url(r'^topics/$', 'topic_list', name='topic_list'),

    # url(r'^(?P<topic_name>[^\.^/]+)/$', 'topic_main', name='topic'),
    url(r'^(?P<topic_slug>[\w-]+)/$', 'topic_main', name='topic'),
    url(r'^(?P<topic_slug>[\w-]+)/new/$', 'topic_main', {'order_by':'new'}, name='topic_new', ),
    url(r'^(?P<topic_slug>[\w-]+)/manage/$', 'topic_manage', name='topic_manage'),
    url(r'^(?P<topic_slug>[\w-]+)/about/$', 'topic_about', name='topic_about'),
)

urlpatterns += patterns('news.links',
    url(r'^submit/$', 'link_submit', name='link_submit_def'),
    url(r'^(?P<topic_slug>[\w-]+)/submit/$', 'link_submit', name='link_submit'),
    url(r'^up/(?P<link_id>\d+)/$', 'upvote_link', name='upvote_link'),
    url(r'^down/(?P<link_id>\d+)/$', 'downvote_link', name='downvote_link'),
    url(r'^save/(?P<link_id>\d+)/$', 'save_link', name='save_link'),
    url(r'^upcomment/(?P<comment_id>\d+)/$', 'upvote_comment', name='upvote_comment'),
    url(r'^downcomment/(?P<comment_id>\d+)/$', 'downvote_comment', name='downvote_comment'),
    url(r'^(?P<topic_name>[^\.^/]+)/comment/(?P<comment_id>\d+)/$', 'comment_detail', name='comment_detail'),
    # url(r'^(?P<topic_name>[^\.^/]+)/(?P<link_id>\d+)/$', 'link_details', name='link_detail'),
    url(r'^(?P<topic_slug>[\w-]+)/(?P<link_slug>[\w-]+)/$', 'link_details', name='link_detail'),
    url(r'^(?P<topic_slug>[\w-]+)/(?P<link_slug>[\w-]+)/info/$', 'link_info', name='link_info'),
    url(r'^(?P<topic_slug>[\w-]+)/(?P<link_slug>[\w-]+)/related/$', 'link_related', name='link_related'),
)
