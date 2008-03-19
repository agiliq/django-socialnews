from django.conf.urls.defaults import *
from django.contrib.auth import views

urlpatterns = patterns('',
    # Example:
    # (r'^implist/', include('implist.foo.urls')),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^login/', views.login),
    
)
