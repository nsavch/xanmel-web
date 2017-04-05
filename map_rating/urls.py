from django.conf.urls import *

from .views import *


urlpatterns = [
    url('^$', map_rating_view, name='map_rating'),
]
