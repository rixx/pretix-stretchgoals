from django.apps import AppConfig


class PluginApp(AppConfig):
    name = 'pretix_avgchart'
    verbose_name = 'A pretix plugin to chart average prices over time'

    class PretixPluginMeta:
        name = 'A pretix plugin to chart average prices over time'
        author = 'Tobias Kunze'
        description = 'Chart the average price of tickets sold over time, and optionally display them publicly.'
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_avgchart.PluginApp'
