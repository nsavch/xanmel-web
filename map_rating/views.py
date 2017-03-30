from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from xanmel.modules.xonotic.models import MapRating, fn, SQL


def server_list(request):
    servers = {}
    for srv in settings.XONOTIC_SERVERS:
        servers[srv['unique_id']] = srv['name']
    return render(request, 'map_rating/server_list.jinja', {'servers': servers})


def server_map_rating(request, server_id):
    server_name = None
    for srv in settings.XONOTIC_SERVERS:
        if server_id == str(srv['unique_id']):
            server_name = srv['name']
            break
    if server_name is None:
        raise Http404
    rating = MapRating.select(MapRating.map,
                              fn.Sum(MapRating.vote).alias('rating'),
                              fn.Avg(MapRating.vote).alias('average'),
                              fn.Count(MapRating.vote).alias('total')) \
        .where(MapRating.server_id == server_id) \
        .group_by(MapRating.map).order_by(SQL('average desc, rating desc'))
    return render(request, 'map_rating/server_map_rating.jinja',
                  {'rating': rating, 'server_name': server_name})
