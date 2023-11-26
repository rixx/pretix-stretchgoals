from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.control.views.event import EventSettingsFormView
from pretix.presale.utils import event_view

from .chart import get_chart_and_text
from .forms import StretchgoalsSettingsForm
from .utils import get_goals, invalidate_cache, set_goals


class ChartMixin:
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        resp[
            "Content-Security-Policy"
        ] = "script-src 'unsafe-eval' 'unsafe-inline'; style-src 'unsafe-inline'"
        return resp

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx.update(get_chart_and_text(self.request.event))

        return ctx


class ControlView(ChartMixin, EventPermissionRequiredMixin, TemplateView):
    template_name = "pretixplugins/stretchgoals/control.html"

    def dispatch(self, request, *args, **kwargs):
        if "refresh" in request.GET:
            invalidate_cache(request.event)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(event_view, name="dispatch")
class PublicView(ChartMixin, TemplateView):
    template_name = "pretixplugins/stretchgoals/public.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.event.settings.stretchgoals_is_public:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class SettingsView(EventSettingsFormView):
    form_class = StretchgoalsSettingsForm
    template_name = "pretixplugins/stretchgoals/settings.html"

    def dispatch(self, request, *args, **kwargs):
        if "delete" in request.GET:
            goals = get_goals(request.event)
            index = int(request.GET.get("delete", 1)) - 1
            goals.pop(index)
            set_goals(request.event, goals)
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse(
            "plugins:pretix_stretchgoals:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
