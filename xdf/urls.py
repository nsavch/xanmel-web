from django.conf.urls import *

from .views import *


urlpatterns = [
    url('^$', main_page, name='main'),
    url('^rating/(\d+)/$', main_rating, name='rating'),
    url('^map/(\d+)/(\d+)/$', map_detail, name='map_detail'),
    url('^compare/(\d+)/$', comparison, name='comparison'),
    url('^news-feed/(\d+)/$', news_feed, name='news_feed'),
]
