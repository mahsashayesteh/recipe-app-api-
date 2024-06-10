
"""
Tests for ingredients api.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)

from recipe.serializers import IngredientSerializer

def details_url(ingredient_id):
    """create and return an ingredient detail url"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])
INGREDIENT_URL = reverse('recipe:ingredient-list')

def create_user(email='user@example.com', password='testpass12'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientApiTest(TestCase):
    """Test unauthenticated API request"""
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """test auth is required for retrieving ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientApiTest(TestCase):
    """Test authenticated API request"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_ingredients(self):
        """Test retierving a list of ingredients"""

        Ingredient.objects.create(user=self.user, name ='kale')
        Ingredient.objects.create(user=self.user, name='vanila')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user"""
        user2 = create_user(email='user2@example.com', password='123')
        Ingredient.objects.create(user=user2, name='salt')
        ingredient = Ingredient.objects.create(user=self.user, name='pepper')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='water')

        payload = {
            'name':'cold water'
        }
        url = details_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])
    
    def test_delete_ingredient(self):
        """Test delete an ingredient. """

        ingredient = Ingredient.objects.create(user=self.user, name='lettuce')
        
        url = details_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredient = Ingredient.objects.all()
        self.assertFalse(ingredient.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """test listing ingredients by those assigned to recipe"""
        ing1 = Ingredient.objects.create(user=self.user, name='eggs')
        ing2 = Ingredient.objects.create(user=self.user, name='carrots')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Kookoo sabzi',
            price=Decimal('90'),
            time_minutes=30,
        )
        
        recipe.ingredients.add(ing1)
        
        res =self.client.get(INGREDIENT_URL,{'assigned_only':1})
        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
        
    
    def test_filtered_ingredients_unique(self):
        ing = Ingredient.objects.create(user=self.user, name='carrot')
        ing2 = Ingredient.objects.create(user=self.user, name='onion')
        r1 = Recipe.objects.create(
            user=self.user,
            title='Carrot rice',
            price=Decimal('90.00'),
            time_minutes=90,
        )
        r2 = Recipe.objects.create(
            user=self.user,
            title='Roasted Carrots',
            price=Decimal('30.8'),
            time_minutes=40,
        )
        r1.ingredients.add(ing)
        r2.ingredients.add(ing)
        
        res = self.client.get(INGREDIENT_URL, {'assigned_only':1})

        self.assertEqual(len(res.data), 1)


      
