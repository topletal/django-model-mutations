import pytest
from django.contrib.auth.models import User, Permission
from django.shortcuts import get_object_or_404
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import db


class ApiClient(Client):
    url = reverse("graphql")

    def query(self, query):
        response = self.post(path=self.url, data={"query": query}, content_type='application/json')
        return response


class UserApiClient(ApiClient):
    @pytest.mark.django_db
    def query_with_permissions(self, query):
        user = User.objects.create_user(username='user', password='pw')
        perm = Permission.objects.get(codename='change_active')
        user.user_permissions.add(perm)
        self.force_login(user)
        return self.query(query)

