from django.views.generic import TemplateView


class ChartView(TemplateView):
    template_name = 'pretixplugins/avgchart/chart.html'


class SettingsView(TemplateView):
    template_name = 'pretixplugins/avgchart/settings.html'
