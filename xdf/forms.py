from django import forms
from django.utils.safestring import mark_safe

from xanmel.modules.xonotic.models import *


class NewsFeedFilterForm(forms.Form):
    event_types = forms.MultipleChoiceField(choices=EventType.choices(),
                                            initial=[i.value for i in EventType],
                                            widget=forms.CheckboxSelectMultiple(),
                                            required=False)
    maps = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'map name matches'}),
                           required=False)
    players = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'player name matches'}),
                              required=False)
    position_lte = forms.IntegerField(required=False,
                                      widget=forms.NumberInput(attrs={'placeholder': 'position <='}))

    def __init__(self, *args, **kwargs):
        servers = list(XDFServer.select(XDFServer.id, XDFServer.name))
        server_ids = [i.id for i in servers]
        kwargs['data'] = kwargs['data'].copy()
        if 'event_types' not in kwargs['data']:
            for i in EventType:
                kwargs['data'].update(event_types=i.value)
        if 'servers' not in kwargs['data']:
            for i in server_ids:
                kwargs['data'].update(servers=i)
        super().__init__(*args, **kwargs)
        self.fields['servers'] = forms.MultipleChoiceField(
            choices=[(i.id, i.name) for i in servers],
            initial=server_ids,
            widget=forms.CheckboxSelectMultiple(),
            required=False)


class MapListOrder(EChoice):
    MAP_NAME_ASC = (0, mark_safe('Map Name &uarr;'))
    MAP_NAME_DESC = (1, mark_safe('Map Name &darr;'))
    PLAYER_ASC = (3, mark_safe('Record Holder &uarr;'))
    PLAYER_DESC = (4, mark_safe('Record Holder &darr;'))
    TIME_ASC = (5, mark_safe('Time &uarr;'))
    TIME_DESC = (6, mark_safe('Time &darr;'))
    TOP_SPEED_PLAYER_ASC = (7, mark_safe('Top Speed Holder &uarr;'))
    TOP_SPEED_PLAYER_DESC = (8, mark_safe('Top Speed Holder &darr;'))
    TOP_SPEED_ASC = (9, mark_safe('Top Speed &uarr;'))
    TOP_SPEED_DESC = (10, mark_safe('Top Speed &darr;'))


class MapListFilterForm(forms.Form):
    maps = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'map name matches'}),
                           required=False)

    def __init__(self, *args, **kwargs):
        servers = list(XDFServer.select(XDFServer.id, XDFServer.name))
        server_ids = [i.id for i in servers]
        if  'servers' not in kwargs['data']:
            kwargs['data'] = kwargs['data'].copy()
            for i in server_ids:
                kwargs['data'].update(servers=i)
        super().__init__(*args, **kwargs)

        self.fields['servers'] = forms.MultipleChoiceField(
            choices=[(i.id, i.name) for i in servers],
            initial=server_ids,
            widget=forms.CheckboxSelectMultiple(),
            required=False)


class MapFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        servers = list(XDFServer.select(XDFServer.id, XDFServer.name))
        server_ids = [i.id for i in servers]
        if 'servers' not in kwargs['data']:
            kwargs['data'] = kwargs['data'].copy()
            for i in server_ids:
                kwargs['data'].update(servers=i)
        super().__init__(*args, **kwargs)
        self.fields['servers'] = forms.MultipleChoiceField(
            choices=[(i.id, i.name) for i in servers],
            initial=server_ids,
            widget=forms.CheckboxSelectMultiple(),
            required=False)


class LadderFilterForm(forms.Form):
    players = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'player name matches'}),
                              required=False)
    ladder_type = forms.ChoiceField(choices=LadderType.choices(), required=False)

    def __init__(self, *args, **kwargs):
        servers = list(XDFServer.select(XDFServer.id, XDFServer.name))
        super().__init__(*args, **kwargs)
        self.fields['server'] = forms.ChoiceField(choices=[(i.id, i.name) for i in servers], required=False)


class CompareWithForm(forms.Form):
    source_player_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = XDFPlayer.select().order_by(XDFPlayer.nickname)
        self.fields['player'] = forms.ChoiceField(choices=[(i.id, i.nickname) for i in players])
