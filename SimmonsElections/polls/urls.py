from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from polls.models import Poll

urlpatterns = patterns('',
    url(r'^$',
        ListView.as_view(
            queryset=Poll.objects.all(),
            context_object_name='latest_poll_list',
            template_name='polls/index.html'),
        name='poll_list'),
    url(r'^(?P<pk>\d+)/$',
        DetailView.as_view(
            model=Poll,
            template_name='polls/detail.html')),
    url(r'^results/$',
        ListView.as_view(
            queryset=Poll.objects.all(),
            context_object_name='latest_poll_list',
            template_name='polls/results.html')),
    url(r'^(?P<poll_id>\d+)/vote/$', 'polls.views.vote'),
)