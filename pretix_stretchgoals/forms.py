import json

from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from i18nfield.forms import (
    I18nForm, I18nFormField, I18nTextarea, I18nTextInput,
)
from pretix.base.forms import SettingsForm
from pretix.base.forms.widgets import DatePickerWidget
from pretix.base.models import Item

from .utils import get_goals, set_goals


class StretchgoalsSettingsForm(I18nForm, SettingsForm):
    # General settings
    stretchgoals_start_date = forms.DateField(
        required=False,
        label=_('Start date'),
        widget=DatePickerWidget(),
        help_text=_('Will start at first sale by default.'),
    )
    stretchgoals_end_date = forms.DateField(
        required=False,
        label=_('End date'),
        widget=DatePickerWidget(),
        help_text=_('Will end at last sale by default.'),
    )
    stretchgoals_items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        required=False,
        label=_('Item types'),
        help_text=_('Items to be included in the calculation.'),
        widget=forms.CheckboxSelectMultiple,
    )
    stretchgoals_include_pending = forms.BooleanField(
        required=False,
        label=_('Include pending orders'),
        help_text=_('By default, only paid orders are included in the calculation.'),
    )

    # Goal settings
    stretchgoals_new_name = I18nFormField(
        required=False, label=_('New goal\'s name'), widget=I18nTextInput
    )
    stretchgoals_new_total = forms.IntegerField(
        required=False, min_value=0, label=_('New total revenue goal')
    )
    stretchgoals_new_amount = forms.IntegerField(
        required=False, min_value=0, label=_('New goal\'s amount of items to be sold')
    )
    stretchgoals_new_description = I18nFormField(
        required=False, label=_('New goal\'s description'), widget=I18nTextarea
    )

    # Display settings
    stretchgoals_is_public = forms.BooleanField(
        required=False,
        label=_('Show publicly'),
        help_text=_('By default, the chart is only shown in the backend.'),
    )
    stretchgoals_calculation_text = forms.BooleanField(
        required=False,
        label=_('Show public text'),
        help_text=_(
            'This text will include the current state and extrapolations for all goals.'
        ),
    )
    stretchgoals_chart_averages = forms.BooleanField(
        required=False,
        label=_('Generate average price graph'),
        help_text=_('This graph shows the development of the average price paid.'),
    )
    stretchgoals_chart_totals = forms.BooleanField(
        required=False,
        label=_('Generate total revenue graph'),
        help_text=_('This graph shows the total revenue over time.'),
    )
    stretchgoals_min_orders = forms.IntegerField(
        required=False,
        label=_('Minimal number of orders'),
        help_text=_(
            'Only show the graph if more than this many orders are taken into consideration.'
        ),
    )
    stretchgoals_public_text = I18nFormField(
        required=False,
        label=_('Text shown on the public page'),
        help_text=_(
            'Text shown on the public page. You can use the placeholder '
            '{avg_now} (the current average).'
        ),
        widget=I18nTextarea,
    )

    def __init__(self, *args, **kwargs):
        """ Reduce possible friends_ticket_items to items of this event. """
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        initial_items = (
            self.event.settings.get('stretchgoals_items', as_type=QuerySet) or []
        )
        if isinstance(initial_items, str) and initial_items:
            initial_items = self.event.items.filter(id__in=initial_items.split(','))
        elif isinstance(initial_items, list):
            initial_items = self.event.items.filter(
                id__in=[i.pk for i in initial_items]
            )

        self.fields['stretchgoals_items'].queryset = Item.objects.filter(
            event=self.event
        )
        self.initial['stretchgoals_items'] = initial_items
        self.goals = get_goals(self.event)

    def _save_new_goal(self):
        goals = json.loads(self.event.settings.get('stretchgoals_goals') or "[]")
        new_goal = dict()
        for item in ['name', 'total', 'amount', 'description']:
            new_goal[item] = self.cleaned_data.pop('stretchgoals_new_{}'.format(item))
            self.fields.pop('stretchgoals_new_{}'.format(item))

        if new_goal['total']:
            goals.append(new_goal)
            set_goals(self.event, goals)

    def save(self, *args, **kwargs):
        self._save_new_goal()
        self.event.settings._h.add_type(
            QuerySet,
            lambda queryset: ','.join([str(element.pk) for element in queryset]),
            lambda pk_list: [
                Item.objects.get(pk=element)
                for element in pk_list.split(',')
                if element
            ],
        )
        super().save(*args, **kwargs)
