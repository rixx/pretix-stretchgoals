from django.conf.urls import url

from .views import ChartView, PublicView, SettingsView

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/avgchart/settings/', SettingsView.as_view(), name='settings'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/avgchart/', ChartView.as_view(), name='chart'),
]

event_patterns = [
    url(r'^stats/', PublicView.as_view(), name='public'),
]
