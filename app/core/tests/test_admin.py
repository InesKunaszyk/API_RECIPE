"""
Test for the DJANGO admin modifications
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

class AdminSiteTest(TestCase):
    """Test for Djnago Admin"""

    def setUp(self):
        """Create a user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email = 'test1@example.com',
            password = 'testpass123456789',
        )

        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email = 'test2@example.com',
            password = 'testpass123456789',
            name = 'User_Test',
        )

    def test_users_list(self):
        """Test checking that users are listed or not"""
        url = reverse('admin:core_user_changelist')
        result = self.client.get(url)

        self.assertContains(result, self.user.name)
        self.assertContains(result, self.user.email)

    def test_edit_user_page(self):
        """test the edit user page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)

    def test_create_user_page(self):
        """Test the create user and page works"""
        url = reverse('admin:core_user_add')
        result = self.client.get(url)

        self.assertEqual(result.status_code, 200)
