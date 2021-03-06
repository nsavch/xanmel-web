import os
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from xanmel.modules.xonotic.models import *


def map_rating_view(request):
    servers = Server.select().order_by(Server.id)
    if request.GET.get('server_id'):
        try:
            active_server = Server.get(id=request.GET['server_id'])
        except DoesNotExist:
            raise Http404
    else:
        active_server = servers[0]
    rating = MapRating.select(Map,
                              fn.Sum(MapRating.vote).alias('rating'),
                              fn.Avg(MapRating.vote).alias('average'),
                              fn.Count(MapRating.vote).alias('total')) \
        .join(Map) \
        .where(Map.server == active_server) \
        .group_by(Map)
    return render(request, 'map_rating/map_rating.jinja', {
        'active_menu': 'map_rating',
        'servers': servers,
        'active_server': active_server,
        'rating': rating
    })


def cointoss_logs(request):
    logs = {}
    for srv in settings.COINTOSS_SERVERS:
        with open(os.path.join(settings.COINTOSS_LOG_DIR, srv + '.log')) as f:
            logs[srv] = ''.join(reversed(f.readlines())).strip()
    return render(request, 'map_rating/cointoss_logs.jinja', {'logs': logs})
