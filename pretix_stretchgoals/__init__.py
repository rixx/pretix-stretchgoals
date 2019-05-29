from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class PluginApp(AppConfig):
    name = 'pretix_stretchgoals'
    verbose_name = ugettext_lazy(
        'Chart the average price of tickets sold over time, and optionally display them publicly.'
    )

    class PretixPluginMeta:
        name = ugettext_lazy('Stretchgoals')
        author = 'Tobias Kunze'
        description = ugettext_lazy(
            'Chart the average price of tickets sold over time, and optionally display them publicly.'
        )
        visible = True
        version = '0.0.1'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_stretchgoals.PluginApp'
