from django.db.models import QuerySet
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from i18nfield.strings import LazyI18nString
from pretix.base.models import Item
from pretix.base.settings import settings_hierarkey
from pretix.base.signals import event_copy_data
from pretix.control.signals import nav_event


@receiver(nav_event, dispatch_uid='stretchgoals_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            'label': _('Stretch Goals'),
            'icon': 'bullseye',
            'url': reverse(
                'plugins:pretix_stretchgoals:control',
                kwargs={
                    'event': request.event.slug,
                    'organizer': request.organizer.slug,
                },
            ),
            'active': url.namespace == 'plugins:pretix_stretchgoals',
        }
    ]


@receiver(signal=event_copy_data, dispatch_uid="stretchgoals_copy_data")
def event_copy_data_receiver(sender, other, item_map, **kwargs):
    other.settings._h.add_type(
        QuerySet,
        lambda queryset: ','.join([str(element.pk) for element in queryset]),
        lambda pk_list: Item.objects.filter(pk__in=pk_list.split(','))
    )
    initial_items = other.settings.get('stretchgoals_items', as_type=QuerySet) or []
    if isinstance(initial_items, str) and initial_items:
        initial_items = [int(i) for i in initial_items.split(',')]
    else:
        initial_items = [i.pk for i in initial_items]
    sender.settings.stretchgoals_items = ','.join(
        str(item_map.get(i).pk) for i in initial_items if i in item_map
    )


settings_hierarkey.add_default('stretchgoals_public_text', '', LazyI18nString)
