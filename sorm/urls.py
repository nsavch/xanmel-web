from django.conf.urls import url

from sorm.views import identity_list, identity_details


app_name = 'sorm'

urlpatterns = [
    url(r'(\d+)/$', identity_details, name='identity-details'),
    url(r'$', identity_list, name='identity-list'),
]
