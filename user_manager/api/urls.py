"""
User APIs for User Manager Application
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from .v1 import urls

urlpatterns = [
    url(r'^v1/', include(urls, namespace='v1')),
]
