#coding=utf-8

from django.conf.urls import url


urlpatterns = [
    url(r'^$', 'restapi.views.document'),

    url(r'^js/client_jquery[.]js$', 'restapi.views.client_jquery'),
    url(r'^js/client_ng[.]js$', 'restapi.views.client_ng'),

    url(r'^debug/$', 'restapi.views.debug'),
]