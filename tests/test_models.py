"""
Tests for User Manager Application models
"""
from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from user_manager.models import UserManagerRole


class UserManagerRoleModelTest(TestCase):
    """
    Tests for UserManagerRole model
    """

    def test_manager_email_property(self):
        user = User.objects.create(username='test', email='test@test.org')
        manager = User.objects.create(username='manager', email='manager@test.org')
        manager_email = 'manager@management.co'

        manager_role_1 = UserManagerRole.objects.create(user=user, manager_user=manager)

        self.assertEqual(manager_role_1.manager_email, manager.email)

        manager_role_2 = UserManagerRole.objects.create(
            user=user,
            unregistered_manager_email=manager_email,
        )

        self.assertEqual(manager_role_2.manager_email, manager_email)

    def test_disallow_user_equal_manager(self):
        user = User.objects.create(username='test', email='test@test.org')

        with self.assertRaises(ValidationError):
            UserManagerRole.objects.create(user=user, manager_user=user)
