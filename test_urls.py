# -*- coding: utf-8 -*-
"""
URLs for completion_aggregator.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import include, url

urlpatterns = [
    url(r'', include('user_manager.api.urls')),
]
