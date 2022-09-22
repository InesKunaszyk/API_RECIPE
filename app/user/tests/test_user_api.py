"""test for user API"""


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**kwargs):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserAPITest(TestCase):
    """test the public feature of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_successfull(self):
        """test creating a user is succesfull"""
        payload = {
            'email': 'newuser@example.com',
            'password': '1234567W89',
            'name': 'NewUserTest',
        }
        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', result.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user email exists already"""
        payload = {
            'email': 'newuser@example.com',
            'password': '1234567W890',
            'name': 'NewUserTest',
        }
        create_user(**payload)
        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test an error is returned if password is too short - less than 10 characters"""
        payload = {
            'email': 'test_password@example.com',
            'password': "123456789",
            'name': 'testName',
        }

        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            'name': 'TestName',
            'email': 'test_TOKEN@example.com',
            'password': 'test-user-token-password123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        result = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """ test return error if credentials invalid """
        create_user(email='test_token@example.com', password='correctpassword')

        payload = {'email': 'token_test@example.com', 'password': 'incorrectpassword'}
        result = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email."""
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)