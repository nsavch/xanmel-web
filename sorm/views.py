import datetime

import dateutil.parser
from collections import defaultdict

from django.contrib.auth.decorators import permission_required
from django.utils import timezone
from django.shortcuts import render

from xanmel.modules.xonotic.models import PlayerIdentification, Server


class IdentityList:
    def __init__(self):
        self.identity_map = {}

    def add_identity(self, identity):
        key = identity.to_key()
        if key in self.identity_map:
            self.identity_map[key]['timestamps'].append(identity.timestamp)
        else:
            self.identity_map[key] = {
                'id': identity.id,
                'timestamps': [identity.timestamp],
                'geo': [],
                'nickname': identity.nickname
            }
        if identity.latitude is not None and identity.longitude is not None:
            already_there = False
            for i in self.identity_map[key]['geo']:
                if abs(identity.latitude - i[0]) < 0.01 and abs(identity.longitude - i[1]) < 0.01:
                    already_there = True
                break
            if not already_there:
                self.identity_map[key]['geo'].append((identity.latitude, identity.longitude))

    def __iter__(self):
        for i in sorted(self.identity_map.items(), key=lambda x: x[1].get('nickname')):
            yield i


@permission_required('can_access_sorm')
def identity_list(request):
    if 'date' in request.GET:
        start_date = dateutil.parser.parse(request.GET['date'])
    else:
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + datetime.timedelta(hours=24)
    # noinspection PyTypeChecker
    raw_identities = PlayerIdentification.select()\
        .join(Server)\
        .where((PlayerIdentification.timestamp > start_date) & (PlayerIdentification.timestamp < end_date))
    print(raw_identities)
    identities = IdentityList()
    for i in raw_identities:
        identities.add_identity(i)
    return render(request, 'sorm/identity_list.jinja', {
        'identities': identities,
        'start_date': start_date,
        'end_date': end_date,
        'prev_date': start_date - datetime.timedelta(hours=24)
    })


def identity_details(request, identity_id):
    pass
