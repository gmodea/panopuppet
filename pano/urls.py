from pano.views.analytics import analytics
from pano.views.dashboard import dashboard
from pano.views.event_analytics import event_analytics
from pano.views.filebucket import filebucket
from pano.views.logout import logout_view
from pano.views.node_facts import facts
from pano.views.nodes import nodes
from pano.views.report_events import detailed_events
from pano.views.reports import reports
from pano.views.splash import splash
from pano.views.api.node_data import nodes_json

__author__ = 'etaklar'

from django.conf.urls import patterns, url

from pano import views

urlpatterns = patterns('',
                       url(r'^$', splash, name='index'),
                       url(r'^login/$', splash, name='login'),
                       url(r'^logout/$', logout_view, name='logout'),
                       url(r'^dashboard/$', dashboard, name='dashboard'),
                       url(r'^filebucket/$', filebucket, name='filebucket'),
                       url(r'^nodes/$', nodes, name='nodes'),
                       url(r'^reports/(?P<certname>[\w\.-]+)/$', reports, name='reports'),
                       url(r'^events/(?P<certname>[\w\.-]+)/(?P<hashid>[\w\.-]+)/$', detailed_events,
                           name='events'),
                       url(r'^analytics/$', analytics, name='analytics'),
                       url(r'^eventanalytics/$', event_analytics, name='event_analytics'),
                       url(r'^eventanalytics/(?P<view>[\w]+)/$', event_analytics, name='event_analytics'),
                       url(r'^facts/(?P<certname>[\w\.-]+)/$', facts, name='facts'),

                       # API URLS
                       url(r'^api/nodes/$', nodes_json, name='api_nodes'),
                       )
