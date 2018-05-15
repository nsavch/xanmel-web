from django.conf.urls import *

from .views import *


app_name = 'xdf'

urlpatterns = [
    url('^$', IndexView.as_view(), name='index'),
    url('^servers/$', ServerListView.as_view(), name='servers'),
    url('^maps/$', MapListView.as_view(), name='maps'),
    url('^maps/(.*)/$', MapView.as_view(), name='map'),
    url('^classic-ladder/$', ClassicLadderView.as_view(), name='classic-ladder')
]
