"""
test for recipe APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')


def create_recipe(user, **kwargs):
    """Create and return a SAMPLE recipe"""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 44,
        'price': Decimal('13.13'),
        'description': 'Tests description',
        'link': 'www.testrecipe.com/recipe1'
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def detail_recipe(recipe_id):
    """"Create and return a recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


class PublicRecipeAPITest(TestCase):
    """Test autheticated API requst"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for API"""
        result = self.client.get(RECIPES_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'testuser@test.com',
            'testpassword123',
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """test retrievieng a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        result = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test list of  recipes is limited to authenticated user"""
        user2 = get_user_model().objects.create_user(
            'user2@example.com',
            'testpassword1234'
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)

        result = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_recipe(recipe.id)
        result = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(result.data, serializer.data)

    def test_create_recipe(self):
        """Testing making new recipe"""
        payload = {
            'title': 'Recipe test',
            'time_minutes': 3,
            'price': Decimal('2.34'),
        }

        result = self.client.post(RECIPES_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=result.data['id'])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of recipe"""
        original_link = "https://.example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title='title for test',
            link=original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_recipe(recipe.id)
        result = self.client.patch(url, payload)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_update(self):
        """test for update a whole recipe"""
        recipe = create_recipe(
            user=self.user,
            title='title for update recipe',
            link='www.example.com/recipe.pdf',
            description='Description for test',
        )

        payload= {'title':'New title',
                  'link': "www.example.com/recipe.pdf",
                  'description': 'Description',
                  'time_minutes': 10,
                  'price': Decimal("53.96")
                  }

        url = detail_recipe(recipe.id)
        result = self.client.put(url, payload)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v, in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
