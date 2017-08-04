from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from i18nfield.forms import I18nForm, I18nFormField, I18nTextarea
from pretix.base.forms import SettingsForm
from pretix.base.models import Item


class StretchgoalsSettingsForm(I18nForm, SettingsForm):
    # General settings
    stretchgoals_start_date = forms.DateField(
        required=False,
        label=_('Start date'),
        help_text=_('Will start at first sale by default.')
    )
    stretchgoals_end_date = forms.DateField(
        required=False,
        label=_('End date'),
        help_text=_('Will end at last sale by default.')
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
        help_text=_('By default, only paid orders are included in the calculation.')
    )

    # Display settings
    stretchgoals_is_public = forms.BooleanField(
        required=False,
        label=_('Show publicly'),
        help_text=_('By default, the chart is only shown in the backend.')
    )
    stretchgoal_chart_averages = forms.BooleanField(
        required=False,
        label=_('Show average price on chart'),
        help_text=_('By default, the chart is plotting total revenue.')
    )
    stretchgoals_public_text = I18nFormField(
        required=False,
        label=_('Text shown on the public page.'),
        help_text=_('Text shown on the public page. You can use the placeholders {target} (the target average), '
                '{avg_now} (the current average), and {avg_required} (the average still required to reach the goal).'),
        widget=I18nTextarea
    )

    def __init__(self, *args, **kwargs):
        """ Reduce possible friends_ticket_items to items of this event. """
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        avg_initial = self.event.settings.get('stretchgoals_items', as_type=QuerySet) or []
        if isinstance(avg_initial, str) and avg_initial:
            avg_initial = self.event.items.filter(id__in=avg_initial.split(','))
        elif isinstance(avg_initial, list):
            avg_initial = self.event.items.filter(id__in=[i.pk for i in avg_initial])

        self.fields['stretchgoals_items'].queryset = Item.objects.filter(event=self.event)
        self.initial['stretchgoals_items'] = avg_initial

    def save(self, *args, **kwargs):
        self.event.settings._h.add_type(
            QuerySet,
            lambda queryset: ','.join([str(element.pk) for element in queryset]),
            lambda pk_list: [Item.objects.get(pk=element) for element in pk_list.split(',') if element]
        )
        super().save(*args, **kwargs)
