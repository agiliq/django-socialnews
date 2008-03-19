from django.conf.urls.defaults import *
from django.contrib.auth import views

urlpatterns = patterns('',
    # Example:
    # (r'^implist/', include('implist.foo.urls')),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^login/$', views.login),
    (r'^login/$', views.logout),
    (r'^register/$', views.login),
    
)

urlpatterns += patterns('news.topics',
    (r'^poll/(?P<slug>[^\.^/]+)/$', 'question'),
    (r'^create_topic/', 'create'),
    (r'^(?P<topic_name>[^\.^/]+)/$', 'topic_main'),
)
