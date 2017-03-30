from django.conf.urls import *

from .views import *


urlpatterns = [
    url('^$', server_list, name='server_list'),
    url('^([^/]*)/map_rating$', server_map_rating, name='server_map_rating')
]
