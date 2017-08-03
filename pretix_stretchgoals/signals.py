from django.core.urlresolvers import resolve, reverse
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from pretix.control.signals import nav_event


@receiver(nav_event, dispatch_uid='stretchgoals_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('Chart Averages'),
        'icon': 'line-chart',
        'url': reverse('plugins:pretix_stretchgoals:chart', kwargs={
            'event': request.event.slug,
            'organizer': request.organizer.slug,
        }),
        'active': url.namespace == 'plugins:pretix_stretchgoals',
    }]
