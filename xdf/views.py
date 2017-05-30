from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from xanmel.modules.xonotic.models import Server, DoesNotExist, XDFTimeRecord, Map, XDFSpeedRecord, JOIN, Player

from .player_rating import PlayerRating


def main_page(request):
    servers = Server.select().where(Server.id << list(settings.XONOTIC_XDF_DATABASES.keys()))
    if request.GET.get('server_id'):
        try:
            active_server = Server.get(id=request.GET['server_id'])
        except DoesNotExist:
            raise Http404
    else:
        active_server = servers[0]
    map_summary = Map.select(Map, XDFTimeRecord, XDFSpeedRecord) \
        .where(Map.server == active_server) \
        .join(XDFTimeRecord, JOIN.LEFT_OUTER, on=XDFTimeRecord.map.alias('time_record')) \
        .switch(Map) \
        .join(XDFSpeedRecord, JOIN.LEFT_OUTER, on=XDFSpeedRecord.map.alias('speed_record')) \
        .where(XDFTimeRecord.position == 1)
    return render(request, 'xdf/main.jinja', {
        'active_menu': 'xdf',
        'servers': servers,
        'active_server': active_server,
        'map_summary': map_summary
    })


def map_detail(request, server_id, map_id):
    servers = Server.select().where(Server.id << list(settings.XONOTIC_XDF_DATABASES.keys()))
    try:
        server = Server.get(id=server_id)
        map = Map.get(Map.server == server, Map.id == map_id)
    except DoesNotExist:
        raise Http404
    try:
        speed_record = XDFSpeedRecord.get(XDFSpeedRecord.map == map)
    except DoesNotExist:
        speed_record = None
    time_records = XDFTimeRecord.select().where(XDFTimeRecord.map == map).order_by(XDFTimeRecord.position)
    rating = PlayerRating(server.id, only_for_map=map.id)
    return render(request, 'xdf/map.jinja', {
        'active_menu': 'xdf',
        'active_server': server,
        'servers': servers,
        'map': map,
        'speed_record': speed_record,
        'time_records': time_records,
        'rating': rating.map_rating_iterations[-1]
    })


def main_rating(request, server_id):
    servers = Server.select().where(Server.id << list(settings.XONOTIC_XDF_DATABASES.keys()))
    try:
        server = Server.get(id=server_id)
    except DoesNotExist:
        raise Http404
    rating = PlayerRating(server.id).total_rating_iterations[-1]
    return render(request, 'xdf/main_rating.jinja', {
        'servers': servers,
        'active_server': server,
        'rating': sorted(rating.items(), key=lambda x: x[1], reverse=True)
    })


def comparison(request, server_id):
    servers = Server.select().where(Server.id << list(settings.XONOTIC_XDF_DATABASES.keys()))
    try:
        server = Server.get(id=server_id)
    except DoesNotExist:
        raise Http404
    player1_id = request.GET.get('player1')
    player2_id = request.GET.get('player2')
    players = Player.select().order_by(Player.nickname)
    if player1_id is None or player2_id is None:
        return render(request, 'xdf/comparison.jinja', {
            'servers': servers,
            'active_server': server,
            'players': players,
            'results': []
        })
    try:
        player1 = Player.get(id=player1_id)
        player2 = Player.get(id=player2_id)
    except DoesNotExist:
        raise Http404
    results = []
    maps = Map.select(Map).where(Map.server == server)
    for i in maps:
        try:
            p1r = XDFTimeRecord.get(XDFTimeRecord.map == i, XDFTimeRecord.player == player1)
        except DoesNotExist:
            p1r = None
        try:
            p2r = XDFTimeRecord.get(XDFTimeRecord.map == i, XDFTimeRecord.player == player2)
        except DoesNotExist:
            p2r = None
        if p1r or p2r:
            if p1r and p2r:
                if p1r.time < p2r.time:
                    gap = (p2r.time - p1r.time) * 100 / p1r.time
                else:
                    gap = (p1r.time - p2r.time) * 100 / p2r.time
                results.append((i, p1r, p2r, gap))
            else:
                gap = None
    return render(request, 'xdf/comparison.jinja', {
        'servers': servers,
        'active_server': server,
        'player1': player1,
        'player2': player2,
        'players': players,
        'results': results
    })
