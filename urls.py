from django.conf.urls import url
from finances.views import *

urlpatterns = [
    url(r'^$', finances_view.as_view(), name='f_home'),
    url(r'^n/$', new_flow.as_view(), name='f_flow_new'),
    url(r'^fe/(?P<slug>[^/]+)/$', view_flow.as_view(), name='f_flow_view'),
    url(r'^fe/(?P<slug>[^/]+)/edit/$', edit_flow.as_view(), name='f_flow_edit'),
    url(r'^fe/(?P<slug>[^/]+)/transaction/$', new_transaction.as_view(), name='f_flow_transaction'),
    url(r'^t/(?P<slug>[^/]+)/$', edit_transaction.as_view(), name='f_transaction_edit'),
    url(r'^t/(?P<slug>[^/]+)/delete/$', delete_transaction.as_view(), name='f_transaction_delete'),
]