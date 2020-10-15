from django.conf.urls import url

from sorm.views import identity_list, identity_details, search_key, advanced_search, dump_cts_records


app_name = 'sorm'

urlpatterns = [
    url(r'(\d+)/$', identity_details, name='identity-details'),
    url(r'key/(.*)/$', search_key, name='search_key'),
    url(r'search/$', advanced_search, name='advanced-search'),
    url(r'cts-records/$', dump_cts_records, name='dump_cts_records'),
    url(r'$', identity_list, name='identity-list'),

]
