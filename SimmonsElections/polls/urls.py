from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from polls.models import Poll, AnswerSet

urlpatterns = patterns('',
#    url(r'^results/$', 'polls.views.results', name='poll_results'),
    url(r'^login_email/$', 'polls.views.login_email', name='polls_login_email'),
    url(r'^login/$', 'polls.views.login', name='login'),
    url(r'^(?P<poll_id>\d+)/$', 'polls.views.vote',
        name='poll_vote'),
)
