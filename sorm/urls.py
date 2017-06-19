from django.conf.urls import url

from sorm.views import identity_list

urlpatterns = [
    url(r'$', identity_list, name='identity_list'),
]
