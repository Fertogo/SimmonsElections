from django.conf.urls import patterns, include, url

from django.contrib import admin
from polls import views as poll_views
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^polls/', include('polls.urls')),
# To end elections:    url((r'^polls/', poll_views.election_index_redirect),

                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^$', poll_views.polls_index_redirect, name = 'election_index'),
)
