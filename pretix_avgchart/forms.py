from django import forms
from pretix.base.forms import SettingsForm


class AvgchartSettingsForm(SettingsForm):
    avgchart_start_date = forms.DateField(
        required=False,
        label=_('Start date'),
        help_text=_('Will start at first sale otherwise.')
    )
    avgchart_end_date = forms.DateField(
        required=False,
        label=_('End date'),
        help_text=_('Will end at last sale otherwise.')
    )
    avgchart_is_public = forms.BooleanField(
        required=False,
        label=_('Show publicly'),
        help_text=_('By default, the chart is only shown in the backend.')
    )
    avgchart_items = forms.ModelMultipleChoiceField(
        required=False,
        Item.objects.all(),
        label=_('Ticket types'),
        help_text=_('Tickets to be included in the calculation.'),
    )
    avgchart_include_pending = forms.BooleanField(
        required=False,
        label=_('Include pending orders'),
        help_text=_('By default, only paid orders are included in the calculation.')
    )
    avgchart_target_value = forms.DecimalField(
        required=False,
        label=_('Target value'),
        help_text=_('Do you need to reach a specific goal?')
    )
    avgchart_public_text = forms.TextField(
        required=False,
        label=_('Text shown on the public page')
    )


    def __init__(self, *args, **kwargs):
        """ Reduce possible friends_ticket_items to items of this event. """
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        self.fields['avgchart_items'].queryset = Item.objects.filter(event=event)
