from datetime import timedelta

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from pretix.base.models import OrderPosition
from pretix.control.views.event import EventSettingsFormView

from .forms import AvgchartSettingsForm


class ChartView(TemplateView):
    template_name = 'pretixplugins/avgchart/chart.html'

    def get_queryset(self, items, include_pending):
        qs = OrderPosition.objects.filter(order__event=self.request.event)
        allowed_states = ['p', 'n'] if include_pending else ['p']
        qs = qs.filter(order__status__in=allowed_states)
        if items:
            qs = qs.filter(item__in=items)
        return qs.order_by('order__datetime')

    def get_start_date(self, items, include_pending):
        return self.get_queryset(items, include_pending).first().order.datetime.date()

    def get_end_date(self, items, include_pending):
        return self.get_queryset(items, include_pending).last().order.datetime.date()

    def get_date_range(self, start_date, end_date):
        for offset in range((end_date - start_date).days + 1):
            yield start_date + timedelta(days=offset)

    def get_context_data(self):
        ctx = super().get_context_data()
        include_pending = self.request.event.settings.avgchart_include_pending or False
        items = self.request.event.settings.avgchart_items or []
        start_date = self.request.event.settings.avgchart_start_date or self.get_start_date(items, include_pending)
        end_date = self.request.event.settings.avgchart_end_date or self.get_end_date(items, include_pending)
        ctx.update({
            'target': self.request.event.settings.avgchart_target_value,
            {
                'date': date,
                'price': self.get_average_price(start_date, date, items, include_pending)
            } for date in self.get_date_range(start_date, end_date)
        })


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
