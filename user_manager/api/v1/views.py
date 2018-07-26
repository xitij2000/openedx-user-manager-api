"""
Views for User Manager Application.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.models import User
from django.db.models import Q

from ...models import UserManagerRole
from .serializers import ManagerListSerializer, ManagerReportsSerializer, UserManagerSerializer


def _filter_by_manager_id_or_email(queryset, identifier):
    """
    Filters provided ``queryset`` by ``manager_id``.
    Here ``manager_id`` can be a username or email address.

    Args:
        queryset(QuerySet): UserManagerRole queryset
        identifier(str): username or email address of manager
    Returns:
        queryset filtered by manager
    """

    if identifier is None:
        return queryset
    elif '@' in identifier:
        return queryset.filter(
            Q(manager_user__email=identifier) | Q(unregistered_manager_email=identifier),
        )
    else:
        return queryset.filter(
            manager_user__username=identifier,
        )


def _filter_by_user_id_or_email(queryset, identifier):
    """
    Filter ``queryset`` by ``identifier``, where ``identifier`` can be a username or email address.

    Args:
        queryset(QuerySet): UserManagerRole queryset
        identifier(str): username or email address of user
    Returns:
        queryset filtered by user
    """

    if identifier is None:
        return queryset
    elif '@' in identifier:
        return queryset.filter(user__email=identifier)
    else:
        return queryset.filter(user__username=identifier)


class ManagerViewMixin(object):
    """
    Provide common functionality for all manager views.
    """

    permission_classes = (IsAuthenticated,)

    @property
    def authentication_classes(self):  # pragma: no cover
        """
        Allow users authenticated via OAuth2 or normal session authentication.
        """
        from openedx.core.lib.api import authentication  # pylint: disable=import-error
        return [
            authentication.OAuth2AuthenticationAllowInactiveUser,
            authentication.SessionAuthenticationAllowInactiveUser,
        ]


class ManagerListView(ManagerViewMixin, ListAPIView):
    """
        **Use Case**

            * Get a list of all users that are managers for other users

        **Get Request**

            GET /api/user_manager/v1/managers/

        **GET Parameters**

            None

        **GET Response**

            If the request for information about the managers is successful, an HTTP 200 "OK"
            response is returned with a collection of managers.

            The HTTP 200 response has the following values.

            * count: The number of managers in a course.

            * next: The URI to the next page of results.

            * previous: The URI to the previous page of results.

            * num_pages: The number of pages.

            * results: a list of manager users:

                * id: The user id for a manager user, or null if manager doesn't have an
                  account yet.

                * email: Email address of manager.

        **Get Response Example**

        ::

            {
                "count": 99,
                "next": "https://courses.example.com/api/user_manager/v1/managers/?page=2",
                "previous": null,
                "results": {
                    {
                        "email": "staff@example.com",
                        "username": "staff"
                    },
                    { ... }
                }
            }
    """

    serializer_class = ManagerListSerializer
    queryset = UserManagerRole.objects.values(
        'manager_user__username',
        'manager_user__email',
        'unregistered_manager_email',
    ).distinct()


class ManagerReportsListView(ManagerViewMixin, ListCreateAPIView):
    """
        **Use Cases**

            * Get a list of all users that are reports for the provided manager.

            * Add a user as a report under a manger.

            * Remove a user or all users under a manager.

        **GET Request**

        ::

            GET /api/user_manager/v1/managers/{user_id}/reports/

        **GET Parameters**

            * user_id: username or email address for user whose reports you want fetch

        **GET Response**

            GET /api/user_manager/v1/managers/{user_id}/reports/

            If the request for information about the managers is successful, an HTTP 200 "OK"
            response is returned with a collection of managers.

            The HTTP 200 response has the following values.

            * count: The number of managers in a course.

            * next: The URI to the next page of results.

            * previous: The URI to the previous page of results.

            * num_pages: The number of pages.

            * results: a list of users under a manager:

                * username: The username for a user.

                * email: Email address of user.

        **GET Response Example**

        ::

            GET /api/user_manager/v1/reports/edx@example.com/reports/

            {
                "count": 99,
                "next": "https://courses.example.com/api/user_manager/v1/reports/edx@example.com/reports/?page=2",
                "previous": null,
                "results": {
                    {
                        "email": "staff@example.com",
                        "username": "staff"
                    },
                    { ... }
                }
            }


        **POST Request**

        ::

            POST /api/user_manager/v1/managers/{user_id}/reports/ {
                "email": "{email}"
            }

        **POST Parameters**

            * user_id: username or email address for user for whom you want to add a manger

            * email: Email address for a user

        **POST Response Example**

        ::

            POST /api/user_manager/v1/reports/edx@example.com/reports/ {
                "email": "user@email.com"
            }

            {
                "email": "user@email.com"
                "username": "user"
            }

        **Delete Requests**

        ::

            DELETE /api/user_manager/v1/managers/{user_id}/reports/

            DELETE /api/user_manager/v1/managers/{user_id}/reports/?user={user_id}

        **DELETE Parameters**

            * user_id: username or email address for user
    """

    serializer_class = ManagerReportsSerializer

    def get_queryset(self):
        """
        Return queryset with username filter.
        """

        username = self.kwargs['username']
        return _filter_by_manager_id_or_email(UserManagerRole.objects, username)

    def perform_create(self, serializer):
        """
        Use serializer to create ``UserManagerRole`` object using provided data.
        """

        manager_id = self.kwargs['username']
        email = serializer.validated_data.get('user', {}).get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFound(detail='No user with that email')

        if '@' in manager_id:
            try:
                manager_user = User.objects.get(email=manager_id)
            except User.DoesNotExist:
                serializer.save(user=user, unregistered_manager_email=manager_id)
                return
        else:
            manager_user = User.objects.get(username=manager_id)

        serializer.save(manager_user=manager_user, user=user)

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Delete one or all reports for provided manager.
        """

        user = request.query_params.get('user')
        queryset = _filter_by_user_id_or_email(self.get_queryset(), user)
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserManagerListView(ManagerViewMixin, ListCreateAPIView):
    """
        **Use Cases**

            * Get a list of the managers that a user directly reports to.

            * Add a manger for a user.

            * Remove all managers for a user, or remove a single manager for a user.

        **GET Request**

        ::

            GET /api/user_manager/v1/users/{user_id}/managers/

        **GET Parameters**

            * user_id: username or email address for user whose managers you want fetch

        **GET Response Values**

            If the request for information about the managers is successful, an HTTP 200 "OK"
            response is returned with a collection of managers.

            The HTTP 200 response has the following values.

            * count: The number of managers in a course.

            * next: The URI to the next page of results.

            * previous: The URI to the previous page of results.

            * num_pages: The number of pages.

            * results: a list of managers directly over a user:

                * username: The username for a manager (may be null if manager hasn't
                  registered an account).

                * email: Email address of manager.

        **GET Response Example**

        ::

            GET /api/user_manager/v1/users/staff@example.com/managers/

            {
                "count": 99,
                "next": "https://courses.example.com/api/user_manager/v1/users/staff@example.com/managers/?page=2",
                "previous": null,
                "results": {
                    {
                        "email": "edx@example.com",
                        "username": "edx"
                    },
                    { ... }
                }
            }

        **POST Request**

        ::

            POST /api/user_manager/v1/users/{user_id}/managers/ {
                "email": "{email}"
            }

        **POST Parameters**

            * user_id: username or email address for user for whom you want to add a manger

            * email: Email address for the manager

        **POST Response Example**

        ::

            POST /api/user_manager/v1/users/edx@example.com/managers/ {
                "email": "user@email.com"
            }

            {
                "email": "user@email.com"
                "username": "user"
            }

        **DELETE Requests**

        ::

            DELETE /api/user_manager/v1/users/{user_id}/managers/

            DELETE /api/user_manager/v1/users/{user_id}/managers/?user={user_id}


        **DELETE Parameters**

            * user_id: username or email address for manager
    """

    serializer_class = UserManagerSerializer

    @staticmethod
    def _get_user_by_username_or_email(identifier):
        """
        Get user by identifier, which could be an email or username.
        """

        if '@' in identifier:
            return User.objects.get(email=identifier)
        else:
            return User.objects.get(username=identifier)

    def get_queryset(self):
        """
        Get queryset filtered by username.
        """

        username = self.kwargs['username']
        return _filter_by_user_id_or_email(UserManagerRole.objects, username)

    def perform_create(self, serializer):
        """
        Use serializer to create ``UserManagerRole`` object using provided data.
        """

        try:
            user = self._get_user_by_username_or_email(self.kwargs['username'])
        except User.DoesNotExist:
            raise NotFound(detail='No user with that email')

        manager_email = serializer.validated_data.get('manager_email')

        try:
            manager = User.objects.get(email=manager_email)
            serializer.save(manager_user=manager, user=user)
        except User.DoesNotExist:
            serializer.save(unregistered_manager_email=manager_email, user=user)

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Delete all manager for supplied user.
        """

        manager = request.query_params.get('manager')
        queryset = _filter_by_manager_id_or_email(self.get_queryset(), manager)
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
