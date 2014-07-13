from django.conf.urls import patterns, include, url

from django.contrib import admin
from polls import views as poll_views
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^closed/', poll_views.polls_closed, name='polls_closed'),                       
#                       url(r'^polls/', poll_views.polls_closed_redirect), #include('polls.urls')),
                       url(r'^polls/', poll_views.results_redirect), 
# To end Elections:
#                       url(r'^polls/', poll_views.polls_closed),
#                       url(r'^closed/', poll_views.polls_closed),
#                       url(r'^polls/', include('polls.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^results/', poll_views.results_index, name='results_index'),
                       url(r'^raw-results/(?P<poll_id>\d+)/$', poll_views.raw_results, name ='raw_results'),                                              
#                       url(r'^$', poll_views.polls_index_redirect, name = ''),
                       url(r'^$', poll_views.results_redirect, name = ''),                       
)
