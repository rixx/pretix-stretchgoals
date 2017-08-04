from datetime import date, timedelta
import decimal
import json

from django.core.urlresolvers import reverse
from django.db.models import Avg, Sum
from django.db.models.query import QuerySet
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import TemplateView
from i18nfield.strings import LazyI18nString
from pretix.base.models import Item, OrderPosition
from pretix.control.views import ChartContainingView
from pretix.control.views.event import EventSettingsFormView
from pretix.presale.utils import event_view

from .forms import StretchgoalsSettingsForm


class AvgChartMixin:

    def get_queryset(self, items, include_pending):
        qs = OrderPosition.objects.filter(order__event=self.request.event)
        allowed_states = ['p', 'n'] if include_pending else ['p']
        qs = qs.filter(order__status__in=allowed_states)
        if items:
            qs = qs.filter(item__in=items)
        return qs.order_by('order__datetime')

    def get_start_date(self, items, include_pending):
        start_date = self.request.event.settings.get('stretchgoals_start_date', as_type=date)
        if start_date:
            return start_date
        first_order = self.get_queryset(items, include_pending).first()
        if first_order:
            return first_order.order.datetime.date()
        else:
            return (now() - timedelta(days=2)).date()

    def get_end_date(self, items, include_pending):
        end_date = self.request.event.settings.get('stretchgoals_end_date', as_type=date)
        if end_date:
            return end_date
        last_order = self.get_queryset(items, include_pending).last()
        if last_order:
            last_date = last_order.order.datetime.date()
            if last_date == now().date():
                last_date -= timedelta(days=1)
        else:
            last_date = (now() - timedelta(days=1)).date()
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

    def get_required_average_price(self, items, include_pending, target):
        if not target:
            return
        all_orders = self.get_queryset(items, include_pending).filter(
            order__datetime__gte=self.get_start_date(items, include_pending),
            order__datetime__lte=self.get_end_date(items, include_pending)
        )
        current_count = all_orders.count()
        total_count = int(self.request.event.settings.get('stretchgoals_items_to_be_sold') or 0)

        current_total = all_orders.aggregate(Sum('price')).get('price__sum') or 0
        goal_total = total_count * target

        if current_total > goal_total:
            return 0

        try:
            return round((goal_total - current_total) / (total_count - current_count), 2)
        except:
            return None

    def get_cache_key(self):
        return 'stretchgoals_data_{}'.format(self.request.event.slug)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx['public_text'] = str(self.request.event.settings.get('stretchgoals_public_text', as_type=LazyI18nString))
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
        include_pending = self.request.event.settings.stretchgoals_include_pending or False
        items = self.request.event.settings.get('stretchgoals_items', as_type=QuerySet) or []
        start_date = self.get_start_date(items, include_pending)
        end_date = self.get_end_date(items, include_pending)
        target_value = decimal.Decimal(self.request.event.settings.stretchgoals_target_value or 0)
        data = {
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': self.get_average_price(start_date, date, items, include_pending) or 0,
            } for date in self.get_date_range(start_date, end_date)],
            'target': float(target_value),
        }
        chart_data = json.dumps(data)

        cache.set(cache_key, chart_data, timeout=3600)
        ctx['data'] = chart_data
        ctx['public_text'] = ctx['public_text'].format(**{
            'target': target_value,
            'avg_now': data['data'][-1]['price'] if data['data'] else None,
            'avg_required': self.get_required_average_price(items, include_pending, target_value)
        })
        return ctx


class ControlView(ChartContainingView, AvgChartMixin, TemplateView):
    template_name = 'pretixplugins/stretchgoals/control.html'

    def get_context_data(self, event=None, organizer=None):
        if 'refresh' in self.request.GET:
            self.request.event.get_cache().delete(self.get_cache_key())
        return super().get_context_data(event=event, organizer=organizer)


@method_decorator(event_view, name='dispatch')
class PublicView(ChartContainingView, AvgChartMixin, TemplateView):
    template_name = 'pretixplugins/stretchgoals/public.html'


class SettingsView(EventSettingsFormView):
    form_class = StretchgoalsSettingsForm
    template_name = 'pretixplugins/stretchgoals/settings.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse('plugins:pretix_stretchgoals:settings', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })
