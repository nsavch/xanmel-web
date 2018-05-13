from django.conf.urls import *

from .views import *


app_name = 'xdf'

urlpatterns = [
    url('^$', IndexView.as_view(), name='main'),

]
