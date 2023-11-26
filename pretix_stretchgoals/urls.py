from django.urls import re_path

from .views import ControlView, PublicView, SettingsView

urlpatterns = [
    re_path(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/settings/stretchgoals/",
        SettingsView.as_view(),
        name="settings",
    ),
    re_path(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/stretchgoals/",
        ControlView.as_view(),
        name="control",
    ),
]

event_patterns = [re_path(r"^stats/", PublicView.as_view(), name="public")]
