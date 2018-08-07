from django.urls import resolve, reverse
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from i18nfield.strings import LazyI18nString

from pretix.base.settings import settings_hierarkey
from pretix.control.signals import nav_event


@receiver(nav_event, dispatch_uid='stretchgoals_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('Stretch Goals'),
        'icon': 'bullseye',
        'url': reverse('plugins:pretix_stretchgoals:control', kwargs={
            'event': request.event.slug,
            'organizer': request.organizer.slug,
        }),
        'active': url.namespace == 'plugins:pretix_stretchgoals',
    }]


settings_hierarkey.add_default('stretchgoals_public_text', '', LazyI18nString)
