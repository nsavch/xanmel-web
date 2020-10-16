import datetime

import dateutil.parser
from collections import defaultdict

from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.utils import timezone
from django.shortcuts import render
from peewee import DoesNotExist, JOIN

from xanmel.modules.xonotic.models import PlayerIdentification, Server, CTSRecord, Map, AnonCTSRecord

from sorm.util import html_colors


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

    def __bool__(self):
        return bool(self.identity_map)

    def __iter__(self):
        for i in sorted(self.identity_map.items(), key=lambda x: x[1].get('nickname')):
            yield i


@permission_required('can_access_sorm')
def identity_list(request):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if 'date' in request.GET:
        start_date = dateutil.parser.parse(request.GET['date'])
    else:
        start_date = today
    end_date = start_date + datetime.timedelta(hours=24)
    # noinspection PyTypeChecker
    raw_identities = PlayerIdentification.select() \
        .where((PlayerIdentification.timestamp > start_date) & (PlayerIdentification.timestamp < end_date))
    identities = IdentityList()
    for i in raw_identities:
        identities.add_identity(i)
    return render(request, 'sorm/identity_list.jinja', {
        'identities': identities,
        'start_date': start_date,
        'end_date': end_date,
        'prev_date': start_date - datetime.timedelta(hours=24),
        'today': today
    })


@permission_required('can_access_sorm')
def identity_details(request, identity_id):
    try:
        identity = PlayerIdentification.get(id=identity_id)
    except DoesNotExist:
        raise Http404
    raw_identities = []
    if 'search' in request.GET:
        search = request.GET['search']
        if search == 'crypto_idfp':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.crypto_idfp == identity.crypto_idfp)
        elif search == 'stats_id':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.stats_id == identity.stats_id)
        elif search == 'raw_nickname':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.raw_nickname == identity.raw_nickname)
        elif search == 'ip_address':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.ip_address == identity.ip_address)
        elif search == 'geoloc':
            raw_identities = PlayerIdentification.select().where(
                (PlayerIdentification.country == identity.country) &
                (PlayerIdentification.subdivisions == identity.subdivisions) &
                (PlayerIdentification.city == identity.city))
        elif search == 'asn':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.asn == identity.asn)
        elif search == 'network':
            raw_identities = PlayerIdentification.select().where(
                PlayerIdentification.network_name == identity.network_name)
    identities = IdentityList()
    for i in raw_identities:
        identities.add_identity(i)
    return render(request, 'sorm/identity_details.jinja', {
        'identity': identity,
        'identities': identities
    })


@permission_required('can_access_sorm')
def search_key(request, crypto_idfp):
    raw_identities = PlayerIdentification.select().where(
        PlayerIdentification.crypto_idfp == crypto_idfp).order_by(PlayerIdentification.timestamp.desc())
    identities = IdentityList()
    for i in raw_identities:
        identities.add_identity(i)
    if raw_identities.count() > 0:
        identity = raw_identities[0]
    else:
        identity = None
    return render(request, 'sorm/identity_details.jinja', {
        'identity': identity,
        'identities': identities
    })


@permission_required('can_access_sorm')
def advanced_search(request):
    query = request.GET.get('query', '')
    if query:
        like_query = '%{}%'.format(query)
        q = ((PlayerIdentification.crypto_idfp ** like_query) |
             (PlayerIdentification.raw_nickname ** like_query) |
             (PlayerIdentification.nickname ** like_query) |
             (PlayerIdentification.ip_address == query))
        try:
            iquery = int(query)
            q |= (PlayerIdentification.stats_id == iquery)
        except (ValueError, TypeError):
            pass
        raw_identities = PlayerIdentification.select().where(q)
        identities = IdentityList()
        for i in raw_identities:
            identities.add_identity(i)
    else:
        identities = None
    return render(request, 'sorm/advanced_search.jinja', {'identities': identities, 'query': query})


@permission_required('can_access_sorm')
def dump_cts_records(request):
    records = CTSRecord.select().join(
        Server,
        JOIN.INNER,
    ).switch(CTSRecord).join(
        Map,
        JOIN.INNER,
    ).order_by(CTSRecord.timestamp.desc())
    return render(request, 'sorm/cts_records.jinja', {
        'records': records,
        'html_colors': html_colors
    })


@permission_required('cann_access_sorm')
def dump_anon_cts_records(request):
    records = AnonCTSRecord.select().join(
        Server,
    ).order_by(AnonCTSRecord.timestamp.desc())
    return render(request, 'sorm/anon_cts_records.jinja', {
        'records': records,
        'html_colors': html_colors,
    })
