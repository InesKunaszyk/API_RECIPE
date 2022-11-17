""""Test for Tags model API"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email='test@test.com', password='testpassword12345'):
    """Create and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """"test auth is required for retrieving tags"""
        result = self.client.get(TAGS_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test authenticated API request"""

    def steUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """test retrieving a list of tags"""
        Tag.objects.create(user=self.user, name="Dessert")
        Tag.objects.create(user=self.user, name="Milk")

        result = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-id')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_tags_limited_to_user(self):
        """test list of tags is limited to uthenticated user"""
        user2 = create_user(email='user2@test.pl')
        Tag.objects.create(user=user2, name='Vegetables')
        tag = Tag.objects.create(user=self.user, name='Fruits')

        result = self.client.get(TAGS_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.datat[0]['name'], tag.name)
        self.assertEqual(result.data[0]['id'], tag.id)