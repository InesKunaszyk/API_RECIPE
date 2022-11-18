"""
test for recipe APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

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


def create_user(**kwargs):
    """Create a new user"""
    return get_user_model().objects.create_user(**kwargs)


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
        self.user = create_user(email='user@example.com', password='password123456')
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
        user2 = create_user(
            email='user2@example.com',
            password='testpassword1234'
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

        payload = {
            'title': 'New title',
            'link': "www.example.com/recipe.pdf",
            'description': 'Description',
            'time_minutes': 10,
            'price': Decimal("53.96"),
        }

        url = detail_recipe(recipe.id)
        result = self.client.put(url, payload)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v, in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in error."""
        new_user = create_user(
            email='mail@mail.com',
            password='1234567890',
        )

        recipe = create_recipe(user=self.user)
        payload = {'user': new_user.id}
        url = detail_recipe(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)

        url = detail_recipe(recipe.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """test trying to delete another users  recipe -  gives ERROR"""
        new_user = create_user(email='user2@user2.pl', password='0987654321')
        recipe = create_recipe(user=new_user)

        url = detail_recipe(recipe.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tag(self):
        """"test for make recipe with NEW tag"""
        payload = {
            'title': 'test tag recipe',
            'time_minutes': 10,
            'price': Decimal('25.66'),
            'tags': [{'name': 'Italian'}, {'name': 'Pasta'}],
        }

        result = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """"test for make recipe with EXISTING tag"""
        tag1 = Tag.objects.create(user=self.user, name='Thai')
        payload = {
            'title': 'Dumplings',
            'time_minutes': 50,
            'price': Decimal(30),
            'tags': [{'name': 'Thai'}, {'name': 'Vege'}],
        }
        result = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
        self.assertTrue(exists)

    def test_create_tag_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Breakfast'}]}
        url = detail_recipe(recipe.id)
        result = self.client.patch(url, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Breakfast')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test asigning an existing tag when updating a recipe"""
        tag_dinner = Tag.objects.create(user=self.user, name='dinner')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_dinner)

        tag_lunch = Tag.objects.create(user=self.user, name='lunch')
        payload = {'tags': [{'name': 'lunch'}]}
        url = detail_recipe(recipe.id)
        result = self.client.patch(url, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_dinner, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """"test clearing a recipe tags"""
        tag = Tag.objects.create(user=self.user, name='dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_recipe(recipe.id)
        result = self.client.patch(url, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_new_recipe_with_new_ingredients(self):
        """"Tests creating and return a recipe with new ingredients"""
        payload = {
            'name': 'Chocolate-fruit shake',
            'time_minutes': 10,
            'price': Decimal('5.48'),
            'ingredients': [
                {'name': 'Cocoa'},
                {'name': 'Banana'},
                {'name': 'Raspberries'},
                {'name': 'plant milk'},
                {'name': 'honey'},
                {'name': 'peanut butter'},
            ]
        }
        result = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 6)

        for ingredient in payload['ingredients']:
            exists = recipe.inggredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name='cheese')
        payload = {
            'name': 'Cheesecake',
            'time_minutes': 60,
            'price': Decimal('25'),
            'ingredients': [
                {'name': 'cheese'},
                {'name': 'sugar'},
                {'name': 'eggs'},
            ]
        }

        result = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
