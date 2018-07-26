"""
Tests for User Manager Application signals
"""
from __future__ import absolute_import, unicode_literals

import mock

from django.test import TestCase

from student.tests.factories import UserFactory
from user_manager.models import UserManagerRole


class UserManagerRoleSignalsTest(TestCase):
    """
    Tests for User Manager Application signals
    """

    def setUp(self):
        self.user = UserFactory()
        self.manager_email = 'manager@management.co'
        UserManagerRole.objects.create(
            user=self.user,
            unregistered_manager_email=self.manager_email,
        )

    @mock.patch('lms.djangoapps.user_manager.signals.upgrade_manager_role_entry')
    def test_upgrade_user_manager_role(self, mock_upgrade_manager_role_entry):
        query = UserManagerRole.objects.filter(user=self.user)

        self.assertEqual(query.count(), 1)

        user_manager_role = query.get()

        self.assertEqual(user_manager_role.unregistered_manager_email, self.manager_email)
        self.assertIsNone(user_manager_role.manager_user)

        manager = UserFactory(email=self.manager_email)
        query = UserManagerRole.objects.filter(user=self.user)

        self.assertEqual(query.count(), 1)

        user_manager_role = query.get()

        self.assertIsNone(user_manager_role.unregistered_manager_email)
        self.assertEqual(user_manager_role.manager_user, manager)

        mock_upgrade_manager_role_entry.assert_called()
