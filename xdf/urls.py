from django.conf.urls import *

from .views import *


app_name = 'xdf'

urlpatterns = [
    url('^$', IndexView.as_view(), name='index'),
    url('^servers/$', ServerListView.as_view(), name='servers'),
    url('^maps/$', MapListView.as_view(), name='maps'),
    url('^maps/(.*)/$', MapView.as_view(), name='map'),
    url('^players/$', ClassicLadderView.as_view(), name='classic-ladder'),
    url(r'^players/(\d+)/$', PlayerView.as_view(), name='player'),
    url(r'^players/(\d+)/activity/$', PlayerActivityView.as_view(), name='player-activity'),
    url(r'^players/(\d+)/records/$', PlayerRecordsView.as_view(), name='player-records'),
    url(r'^players/compare/$', CompareView.as_view(), name='compare')
]
