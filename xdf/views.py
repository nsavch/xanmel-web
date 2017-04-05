from django.http import Http404
from django.shortcuts import render
from django.conf import settings

from .server_db import ServerDB


def server_list(request):
    return render('xdf/server_list.jinja', {'servers': settings.XONOTIC_XDF_DATABASES.keys()})


def map_list(request, server_name):
    if server_name not in settings.XONOTIC_XDF_DATABASES:
        raise Http404
    with open(settings.XONOTIC_XDF_DATABASES[server_name], 'r') as f:
        db = ServerDB.parse(f.read())
    return render('xdf/map_list.jinja', {'maps': db.maps})


def map_detail(request, server_name, map_name):
    if server_name not in settings.XONOTIC_XDF_DATABASES:
        raise Http404
    with open(settings.XONOTIC_XDF_DATABASES[server_name], 'r') as f:
        db = ServerDB.parse(f.read())
    if map_name not in db.maps:
        raise Http404
    return render('xdf/map_detail.jinja', {'map_data': db.maps[map_name]})
