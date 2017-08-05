import json
from datetime import date, timedelta

from django.db.models import Avg, Sum
from django.db.models.query import QuerySet
from django.utils.timezone import now
from i18nfield.strings import LazyI18nString
from pretix.base.models import Item, OrderPosition

from .json import ChartJSONEncoder
from .utils import get_cache_key


def get_queryset(event, items, include_pending):
    qs = OrderPosition.objects.filter(order__event=event)
    allowed_states = ['p', 'n'] if include_pending else ['p']
    qs = qs.filter(order__status__in=allowed_states)
    if items:
        qs = qs.filter(item__in=items)
    return qs.order_by('order__datetime')


def get_start_date(event, items, include_pending):
    start_date = event.settings.get('stretchgoals_start_date', as_type=date)
    if start_date:
        return start_date
    first_order = get_queryset(event, items, include_pending).first()
    if first_order:
        return first_order.order.datetime.date()
    else:
        return (now() - timedelta(days=2)).date()


def get_end_date(event, items, include_pending):
    end_date = event.settings.get('stretchgoals_end_date', as_type=date)
    if end_date:
        return end_date
    last_order = get_queryset(event, items, include_pending).last()
    if last_order:
        last_date = last_order.order.datetime.date()
        if last_date == now().date():
            last_date -= timedelta(days=1)
    else:
        last_date = (now() - timedelta(days=1)).date()
    return last_date


def get_date_range(start_date, end_date):
    for offset in range((end_date - start_date).days + 1):
        yield start_date + timedelta(days=offset)


def get_average_price(event, start_date, end_date, items, include_pending):
    qs = get_queryset(event, items, include_pending).filter(
        order__datetime__date__gte=start_date,
        order__datetime__date__lte=end_date
    )
    return round(qs.aggregate(Avg('price')).get('price__avg') or 0, 2)


def get_total_price(event, start_date, end_date, items, include_pending):
    qs = get_queryset(event, items, include_pending).filter(
        order__datetime__date__gte=start_date,
        order__datetime__date__lte=end_date
    )
    return round(qs.aggregate(Sum('price')).get('price__sum') or 0, 2)


def get_required_average_price(event, items, include_pending, target):
    if not target:
        return
    all_orders = get_queryset(event, items, include_pending).filter(
        order__datetime__gte=get_start_date(event, items, include_pending),
        order__datetime__lte=get_end_date(event, items, include_pending)
    )
    current_count = all_orders.count()
    total_count = int(event.settings.get('stretchgoals_items_to_be_sold') or 0)

    current_total = all_orders.aggregate(Sum('price')).get('price__sum') or 0
    goal_total = total_count * target

    if current_total > goal_total:
        return 0

    try:
        return round((goal_total - current_total) / (total_count - current_count), 2)
    except Exception as e:
        return None


def get_public_text(event, items, include_pending, target_value, data=None):
    text = str(event.settings.get('stretchgoals_public_text', as_type=LazyI18nString))
    if data:
        text = text.format(**{
            'target': data['avg_data']['target'],
            'avg_now': data['avg_data']['data'][-1]['price'] if data['avg_data'] else None,
            'avg_required': get_required_average_price(event, items, include_pending, target_value)
        })
    return text


def get_chart_and_text(event):
    cache = event.get_cache()
    cache_key = get_cache_key(event)
    chart_data = cache.get(cache_key)
    public_text = cache.get(cache_key + '_text')
    if chart_data:
        return chart_data, public_text

    include_pending = event.settings.stretchgoals_include_pending or False
    avg_chart = event.settings.stretchgoals_chart_averages or False
    total_chart = event.settings.stretchgoals_chart_totals or False
    event.settings._h.add_type(
        QuerySet,
        lambda queryset: ','.join([str(element.pk) for element in queryset]),
        lambda pk_list: [Item.objects.get(pk=element) for element in pk_list.split(',') if element]
    )
    items = event.settings.get('stretchgoals_items', as_type=QuerySet) or []
    target_value = 0

    start_date = get_start_date(event, items, include_pending)
    end_date = get_end_date(event, items, include_pending)
    data = {
        'avg_data': {
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': get_average_price(event, start_date, date, items, include_pending) or 0,
            } for date in get_date_range(start_date, end_date)] if avg_chart else None,
            'target': float(target_value),
        },
        'total_data': {
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': get_total_price(event, start_date, date, items, include_pending) or 0,
            } for date in get_date_range(start_date, end_date)] if total_chart else None,
            'target': float(target_value),
        },
    }
    chart_data = {
        key: json.dumps(value, cls=ChartJSONEncoder) for key, value in data.items()
    }
    public_text = get_public_text(event, items, include_pending, target_value, data=data)

    cache.set(cache_key, chart_data, timeout=3600)
    cache.set(cache_key + '_text', public_text, timeout=3600)
    return chart_data, public_text
