from datetime import date, timedelta
import json

from django.core.urlresolvers import reverse
from django.db.models import Avg
from django.db.models.query import QuerySet
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import TemplateView
from pretix.base.models import Item, OrderPosition
from pretix.control.views import ChartContainingView
from pretix.control.views.event import EventSettingsFormView
from pretix.presale.utils import event_view
from pretix.presale.views import EventViewMixin

from .forms import AvgchartSettingsForm


class AvgChartMixin:

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
        last_date = self.get_queryset(items, include_pending).last().order.datetime.date()
        if last_date == now().date():
            last_date -= timedelta(days=1)
        return last_date

    def get_date_range(self, start_date, end_date):
        for offset in range((end_date - start_date).days + 1):
            yield start_date + timedelta(days=offset)

    def get_average_price(self, start_date, end_date, items, include_pending):
        qs = self.get_queryset(items, include_pending).filter(
            order__datetime__date__gte=start_date,
            order__datetime__date__lte=end_date
        )
        return round(qs.aggregate(Avg('price')).get('price__avg') or 0, 2)

    def get_cache_key(self):
        return 'avgchart_data_{}'.format(self.request.event.slug)

    def get_context_data(self, organizer, event):
        ctx = super().get_context_data()
        cache = self.request.event.get_cache()
        cache_key = self.get_cache_key()

        try:
            chart_data = cache.get(cache_key)
        except:
            chart_data = None

        if chart_data:
            ctx['data'] = chart_data
            return ctx

        self.request.event.settings._h.add_type(
            QuerySet,
            lambda queryset: ','.join([str(element.pk) for element in queryset]),
            lambda pk_list: [Item.objects.get(pk=element) for element in pk_list.split(',') if element]
        )
        include_pending = self.request.event.settings.avgchart_include_pending or False
        items = self.request.event.settings.get('avgchart_items', as_type=QuerySet) or []
        start_date = self.request.event.settings.get('avgchart_start_date', as_type=date) or self.get_start_date(items, include_pending)
        end_date = self.request.event.settings.get('avgchart_end_date', as_type=date) or self.get_end_date(items, include_pending)
        chart_data = json.dumps({
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': self.get_average_price(start_date, date, items, include_pending) or 0,
            } for date in self.get_date_range(start_date, end_date)],
            'target': self.request.event.settings.avgchart_target_value
        })

        cache.set(cache_key, chart_data, timeout=3600)
        ctx['data'] = chart_data
        return ctx


class ChartView(ChartContainingView, AvgChartMixin, TemplateView):
    template_name = 'pretixplugins/avgchart/chart.html'

    def get_context_data(self, event=None, organizer=None):
        if 'refresh' in self.request.GET:
            self.request.event.get_cache().delete(self.get_cache_key())
        return super().get_context_data(event=event, organizer=organizer)


@method_decorator(event_view, name='dispatch')
class PublicView(ChartContainingView, AvgChartMixin, TemplateView):
    template_name = 'pretixplugins/avgchart/public.html'


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
