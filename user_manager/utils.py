"""
Utilities for User Manager Application.
"""
from __future__ import absolute_import, unicode_literals

from .models import UserManagerRole


def create_user_manager_role(user, manager_user=None, manager_email=None):
    """
    Create new ``UserManagerRole`` given a ``user`` and a ``manager_user`` or ``manager_email``.
    """
    if manager_email is not None:
        obj, _ = UserManagerRole.objects.get_or_create(
            unregistered_manager_email=manager_email,
            user=user,
        )
    elif manager_user is not None:
        obj, _ = UserManagerRole.objects.get_or_create(
            manager_user=manager_user,
            user=user
        )
    else:
        raise ValueError('Both manager_user and manager_email cannot be None')
    return obj
