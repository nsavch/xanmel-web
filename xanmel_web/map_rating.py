from flask import Blueprint, current_app, render_template, abort
from peewee import fn

from xanmel.modules.xonotic.models import *

map_rating = Blueprint('map_rating', __name__)


@map_rating.route('/')
def server_list():
    return render_template('map_rating/server_list.jinja', servers=current_app.servers)


@map_rating.route('/<server_id>/map-rating')
def server_map_rating(server_id):
    server_name = None
    for i, n in current_app.servers.items():
        if server_id == str(i):
            server_name = n
            break
    if server_name is None:
        abort(404)
    rating = MapRating.select(MapRating.map,
                              fn.Sum(MapRating.vote).alias('rating'),
                              fn.Avg(MapRating.vote).alias('average'),
                              fn.Count(MapRating.vote).alias('total'))\
        .where(MapRating.server_id == server_id)\
        .group_by(MapRating.map).order_by(SQL('average desc, rating desc'))
    return render_template('map_rating/server_map_rating.jinja', rating=rating, server_name=server_name)
