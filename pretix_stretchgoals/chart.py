import json
from datetime import date, timedelta

from django.db.models import Avg, Sum
from django.db.models.query import QuerySet
from django.utils.timezone import now
from i18nfield.strings import LazyI18nString
from pretix.base.models import Item, OrderPosition

from .json import ChartJSONEncoder
from .utils import get_cache_key, get_goals


def get_queryset(event, items, include_pending):
    qs = OrderPosition.objects.filter(order__event=event)
    allowed_states = ['p', 'n'] if include_pending else ['p']
    qs = qs.filter(order__status__in=allowed_states)
    if items:
        qs = qs.filter(item__in=items)
    if include_pending:
        return qs.order_by('order__datetime')
    return qs.order_by('order__payment_date')


def get_start_date(event, items, include_pending):
    start_date = event.settings.get('stretchgoals_start_date', as_type=date)
    if start_date:
        return start_date
    first_order = get_queryset(event, items, include_pending).first()
    if first_order:
        if include_pending:
            return first_order.order.datetime.date()
        return first_order.order.payment_date.date()
    else:
        return (now() - timedelta(days=2)).date()


def get_end_date(event, items, include_pending):
    end_date = event.settings.get('stretchgoals_end_date', as_type=date)
    if end_date:
        return end_date
    last_order = get_queryset(event, items, include_pending).last()
    if last_order:
        if include_pending:
            last_date = last_order.order.datetime.date()
        else:
            last_date = last_order.order.payment_date.date()
        if last_date == now().date():
            last_date -= timedelta(days=1)
    else:
        last_date = (now() - timedelta(days=1)).date()
    return last_date


def get_date_range(start_date, end_date):
    for offset in range((end_date - start_date).days + 1):
        yield start_date + timedelta(days=offset)


def get_average_price(event, start_date, end_date, items, include_pending):
    if include_pending:
        qs = get_queryset(event, items, include_pending).filter(
            order__datetime__date__gte=start_date,
            order__datetime__date__lte=end_date
        )
    else:
        qs = get_queryset(event, items, include_pending).filter(
            order__payment_date__date__gte=start_date,
            order__payment_date__date__lte=end_date
        )
    return round(qs.aggregate(Avg('price')).get('price__avg') or 0, 2)


def get_total_price(event, start_date, end_date, items, include_pending):
    if include_pending:
        qs = get_queryset(event, items, include_pending).filter(
            order__datetime__date__gte=start_date,
            order__datetime__date__lte=end_date
        )
    else:
        qs = get_queryset(event, items, include_pending).filter(
            order__payment_date__date__gte=start_date,
            order__payment_date__date__lte=end_date
        )
    return round(qs.aggregate(Sum('price')).get('price__sum') or 0, 2)


def get_required_average_price(event, items, include_pending, target, total_count, total_now):
    if not target:
        return
    if include_pending:
        all_orders = get_queryset(event, items, include_pending).filter(
            order__datetime__date__gte=get_start_date(event, items, include_pending),
            order__datetime__date__lte=get_end_date(event, items, include_pending)
        )
    else:
        all_orders = get_queryset(event, items, include_pending).filter(
            order__payment_date__date__gte=get_start_date(event, items, include_pending),
            order__payment_date__date__lte=get_end_date(event, items, include_pending)
        )
    current_count = all_orders.count()

    if total_now > target:
        return 0

    try:
        return round((target - total_now) / (total_count - current_count), 2)
    except Exception as e:
        return None


def get_public_text(event, items, include_pending, data=None):
    text = str(event.settings.get('stretchgoals_public_text', as_type=LazyI18nString))
    if data:
        text = text.format(**{
            'avg_now': data['avg_now']
        })
    return text


def get_chart_and_text(event):
    cache = event.get_cache()
    cache_key = get_cache_key(event)
    chart_data = cache.get(cache_key)
    if chart_data:
        return chart_data

    result = {}
    include_pending = event.settings.stretchgoals_include_pending or False
    avg_chart = event.settings.stretchgoals_chart_averages or False
    total_chart = event.settings.stretchgoals_chart_totals or False
    event.settings._h.add_type(
        QuerySet,
        lambda queryset: ','.join([str(element.pk) for element in queryset]),
        lambda pk_list: [Item.objects.get(pk=element) for element in pk_list.split(',') if element]
    )
    items = event.settings.get('stretchgoals_items', as_type=QuerySet) or []

    start_date = get_start_date(event, items, include_pending)
    end_date = get_end_date(event, items, include_pending)
    goals = get_goals(event)
    data = {
        'avg_data': {
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': get_average_price(event, start_date, date, items, include_pending) or 0,
            } for date in get_date_range(start_date, end_date)] if avg_chart else None,
            'target': [goal.get('avg', 0) for goal in goals],
            'label': 'avg',
        },
        'total_data': {
            'data': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': get_total_price(event, start_date, date, items, include_pending) or 0,
            } for date in get_date_range(start_date, end_date)] if total_chart else None,
            'target': [goal['total'] for goal in goals],
            'label': 'total',
        },
    }
    result['data'] = {key: json.dumps(value, cls=ChartJSONEncoder) for key, value in data.items()}
    try:
        result['avg_now'] = data['avg_data']['data'][-1]['price']
        result['total_now'] = data['total_data']['data'][-1]['price']
    except (TypeError, IndexError):  # no data, data[-1] does not exist
        result['avg_now'] = 0
        result['total_now'] = 0

    for goal in goals:
        goal['avg_required'] = get_required_average_price(event, items, include_pending, goal['total'], goal['amount'], result['total_now'])
        goal['total_left'] = goal['total'] - result['total_now']

    result['goals'] = goals
    result['significant'] = (
        not event.settings.stretchgoals_min_orders
        or get_queryset(event, items, include_pending).count() >= event.settings.get('stretchgoals_min_orders', as_type=int)
    )
    result['public_text'] = get_public_text(event, items, include_pending, data=result)
    cache.set(cache_key, result, timeout=3600)
    return result
