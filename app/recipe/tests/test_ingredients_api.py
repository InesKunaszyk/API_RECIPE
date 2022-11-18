"""tests for ingredient model API"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='password12345'):
    """create and return a new user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientApiTests(TestCase):
    """Test unauthorized API request """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(INGREDIENTS_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authorized API request """

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Tests retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='chocolate')
        Ingredient.objects.create(user=self.user, name='honey')

        result = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """"""
        user2 = create_user(email='user2@example.com', password='user2password')
        Ingredient.objects.create(user=user2, name='chilli')
        ingredient = Ingredient.objects.create(user=self.user, name='milk')

        result = self.client.get(INGREDIENTS_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]['name'], ingredient.name)
        self.assertEqual(result.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """test update ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')

        payload = {'name': 'Salt'}
        url = detail_url(ingredient.id)
        result = self.client.patch(url, payload)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """"test deleting ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')

        url = detail_url(ingredient.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
