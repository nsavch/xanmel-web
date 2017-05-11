from django.conf.urls import *

from .views import *


urlpatterns = [
    url('^$', main_page, name='main'),
    url('^rating/(\d+)/$', main_rating, name='rating'),
    url('^map/(\d+)/(\d+)/$', map_detail, name='map_detail')
]
