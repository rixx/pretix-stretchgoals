from django.conf.urls import url

from .views import ControlView, PublicView, SettingsView

urlpatterns = [
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/stretchgoals/settings/',
        SettingsView.as_view(),
        name='settings',
    ),
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/stretchgoals/',
        ControlView.as_view(),
        name='control',
    ),
]

event_patterns = [url(r'^stats/', PublicView.as_view(), name='public')]
