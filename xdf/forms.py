from django import forms

from xanmel.modules.xonotic.models import *


class NewsFeedFilterForm(forms.Form):
    event_types = forms.MultipleChoiceField(choices=EventType.choices(),
                                            initial=[i.value for i in EventType],
                                            widget=forms.CheckboxSelectMultiple(),
                                            required=False)
    maps = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'maps'}),
                           required=False)
    players = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'players'}),
                              required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        servers = list(XDFServer.select(XDFServer.id, XDFServer.name))
        self.fields['servers'] = forms.MultipleChoiceField(
            choices=[(i.id, i.name) for i in servers],
            initial=[i.id for i in servers],
            widget=forms.CheckboxSelectMultiple(),
            required=False
        )

