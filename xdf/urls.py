from django.conf.urls import *

from .views import *


urlpatterns = [
    url('^$', main_page, name='main'),
    url('^map/(\d+)/(\d+)/$', map_detail, name='map_detail')
]
