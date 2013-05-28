from django.conf.urls import patterns, include

urlpatterns = patterns('',
    # Example:
    (r'^', include('news.urls'))
    # (r'^news/', include('news.foo.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
