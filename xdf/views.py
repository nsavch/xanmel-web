from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from xanmel.modules.xonotic.models import Server, DoesNotExist, XDFTimeRecord, Map, XDFSpeedRecord, JOIN


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
    return render(request, 'xdf/map.jinja', {
        'active_menu': 'xdf',
        'active_server': server,
        'servers': servers,
        'map': map,
        'speed_records': speed_record,
        'time_records': time_records
    })
