"""
Tests for User Manager Application views
"""
from __future__ import absolute_import, unicode_literals

import json

import ddt
from mock import PropertyMock, patch
from rest_framework.authentication import SessionAuthentication

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from user_manager.api.v1.views import ManagerViewMixin
from user_manager.models import UserManagerRole


@ddt.ddt
class UserManagerRoleViewsTest(TestCase):
    """
    Tests for User Manager Application views
    """

    @staticmethod
    def _create_users():
        for idx in range(10):
            username = 'report{}'.format(idx)
            email = '{username}@somecorp.com'.format(username=username)
            yield User.objects.create(username=username, email=email)

    @staticmethod
    def _create_managers():
        for idx in range(2):
            username = 'manager{}'.format(idx)
            email = '{username}@somecorp.com'.format(username=username)
            yield User.objects.create(username=username, email=email)

    def setUp(self):
        self.user = User.objects.create(username='staff', email='staff@example.org', is_staff=True)
        self.user.set_password('test')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password='test')
        self.users = list(self._create_users())
        self.managers = list(self._create_managers())
        for user in self.users[:5]:
            UserManagerRole.objects.create(manager_user=self.managers[0], user=user)
        for user in self.users[5:]:
            UserManagerRole.objects.create(manager_user=self.managers[1], user=user)

        UserManagerRole.objects.create(manager_user=self.managers[1], user=self.users[0])

        patcher = patch.object(
            ManagerViewMixin,
            'authentication_classes',
            new_callable=PropertyMock,
            return_value=[SessionAuthentication]
        )
        patcher.start()
        self.addCleanup(patcher.__exit__, None, None, None)

    def test_no_duplicate_managers(self):
        response = self.client.get(reverse('v1:managers-list'))
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 2)

    @ddt.data('username', 'email')
    def test_manager_reports_list_get(self, attr):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': getattr(self.managers[0], attr)},
        )
        response = self.client.get(url)
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 5)

    def test_manager_reports_list_post_duplicate(self):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.post(url, {'email': self.users[0].email})
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 5)

    def test_manager_reports_list_post_nonexistent(self):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        response = self.client.post(url, {'email': 'non@existent.com'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, '{"detail":"No user with that email"}')

    def test_manager_reports_list_delete_all(self):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.delete(url)
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 0)

    def test_manager_reports_list_delete_single(self):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.delete(
            '{url}?user={email}'.format(url=url, email=self.users[0].email)
        )
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 4)
        self.assertNotIn(self.users[0].email, query.values_list('user__email', flat=True))

    def test_manager_reports_list_delete_nonexistent(self):
        url = reverse(
            'v1:manager-reports-list',
            kwargs={'username': self.managers[0].email},
        )
        self.client.delete(
            '{url}?user={email}'.format(url=url, email='non@existent.com')
        )
        query = UserManagerRole.objects.filter(manager_user=self.managers[0])
        self.assertEqual(query.count(), 5)

    @ddt.data('username', 'email')
    def test_user_managers_list_get(self, attr):
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': getattr(self.users[0], attr)},
        )
        response = self.client.get(url)
        data = json.loads(response.content)
        results = data['results']
        self.assertEqual(len(results), 2)

    def test_user_managers_list_post_duplicate(self):
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.post(url, {'email': self.managers[0].email})
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 2)

    def test_user_managers_list_post_unregistered(self):
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.post(url, {'email': 'unregistered@user.com'})
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 3)
        self.assertIn(
            'unregistered@user.com',
            query.values_list('unregistered_manager_email', flat=True),
        )

    def test_user_managers_list_delete_all(self):
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.delete(url)
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 0)

    def test_user_managers_list_delete_single(self):
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 2)
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.delete(
            '{url}?manager={email}'.format(url=url, email=self.managers[0].email)
        )
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 1)
        self.assertNotIn(
            self.managers[0].email,
            query.values_list('manager_user__email', flat=True),
        )

    def test_user_managers_list_delete_nonexistent(self):
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 2)
        url = reverse(
            'v1:user-managers-list',
            kwargs={'username': self.users[0].email},
        )
        self.client.delete(
            '{url}?manager={email}'.format(url=url, email='non@existent.com')
        )
        query = UserManagerRole.objects.filter(user=self.users[0])
        self.assertEqual(query.count(), 2)
