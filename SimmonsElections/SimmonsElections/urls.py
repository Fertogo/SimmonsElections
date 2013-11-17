from django.conf.urls import patterns, include, url

from django.contrib import admin
from polls import views as poll_views
admin.autodiscover()

urlpatterns = patterns('',
# To end Elections:
#                       url(r'^polls/', poll_views.polls_closed),
                       url(r'^closed/', poll_views.polls_closed),                       
                       url(r'^polls/', include('polls.urls')),

                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^$', poll_views.polls_index_redirect, name = 'election_index'),
)
