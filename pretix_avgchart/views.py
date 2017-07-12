from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from pretix.control.views.event import EventSettingsFormView

from .forms import AvgchartSettingsForm


class ChartView(TemplateView):
    template_name = 'pretixplugins/avgchart/chart.html'


class SettingsView(EventSettingsFormView):
    form_class = AvgchartSettingsForm
    template_name = 'pretixplugins/avgchart/settings.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse('plugins:pretix_avgchart:settings', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })
