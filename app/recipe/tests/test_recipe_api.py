"""
Tests for recipe APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

import os
import tempfile

from PIL import Image

from core.models import (
    Recipe, 
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse('recipe:recipe-list')

def create_recipe(user, **params):
    """Create and return a sample recipe. """
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes':22,
        'price':Decimal('5.25'),
        'description': 'Sample recipe description',
        'link': 'http://example.com/recipe.pdf/',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)

def detail_url(recipe_id):
    """Create and return arecipe detail url. """
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_uploads_url(recipe_id):
    """Create and return an image upload url."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests. """

    def setup(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for call api"""

        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests. """
    
    def setUp(self):
        self.user = create_user(
            email = 'test@example.com',
            password = 'testpass123',
            name = 'Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user = self.user)

    
    def test_retrive_recipes(self):
        """Test retriving a list of recipes. """
        
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        
        res = self.client.get(RECIPE_URL)
        
        recpies = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recpies, many = True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
    
    def test_recipe_list_limited_to_user(self):
      
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'testpass123',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user = self.user)
        serializer = RecipeSerializer(recipes, many = True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
    
    def test_get_recipe_details(self):
        recipe = create_recipe(user=self.user)
        
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serilizer = RecipeDetailSerializer(recipe)
        self.assertEqual(serilizer.data, res.data)
        
    def test_create_recipe(self):
        """Test create recipe. """

        payload = {
            'title':'sample title',
            'time_minutes':33,
            'price':Decimal('3.55'),
        }

        res = self.client.post(RECIPE_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        
        for k , v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        
        self.assertEqual(recipe.user, self.user)
    def test_partial_update(self):
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user = self.user,
            title = 'sample title',
            link = original_link,
        )

        pyload = {
            'title':'new sample title'
        }
        url =detail_url(recipe.id)
        res = self.client.patch(url, pyload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.link , original_link)
        self.assertEqual(recipe.user, self.user)
    
    def test_full_update(self):
        recipe = create_recipe(
            user = self.user, 
            title = 'sample title',
            link = 'https://example.com/recipe.pdf',
            description = 'sample description',
        )

        payload = {
            'title':'new title',
            'time_minutes':23,
            'price':Decimal('5.5'),
            'description':'new description',
            'link': 'https://example.com/recipe.pdf'
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k , v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
    
    def test_update_user_returns_error(self):
        """Test changing recipe user result in an error. """
        new_user = create_user(email = 'test2@example.com', password = 'test2pass123')
        recipe = create_recipe(user = self.user)
        payload = {
            'user':new_user,
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_recipe_delete(self):
        """Test deleting a recipe successful. """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test tying to delete another user recipe gives error. """

        new_user = create_user(email= 'test12@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating recipe with new tags. """
        payload = {
            'title':'special',
            'time_minutes':45,
            'price':Decimal('45.88'),
            'tags':[{'name':'thai'}, {'name':'Dinner'}],
        }        
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exits = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exits)
    
    def test_create_recipe_with_existing_tag(self):
        tag_indian = Tag.objects.create(user= self.user, name='Indian')
        payload = {
            'title':'Pongal',
            'time_minutes':68,
            'price':Decimal('4.50'),
            'tags':[{'name':'Indian'}, {'name':'Breakfast'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exits = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            )
            self.assertTrue(exits)

    def test_create_tag_on_update(self):
        """test creating tag when updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {
            'tags':[{'name':'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user = self.user, name='breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user = self.user, name= 'Lunch')
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clear_recipe_tags(self):
        """test clearing recipe's tags"""
        tag = Tag.objects.create(user= self.user, name='lunch')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredient(self):
        """Test creating an recipe with new ingredients """
        payload = {
            'title':'Cauliflowers Tacos',
            'time_minutes': 300,
            'price':'3.45',
            'ingredients':[{'name':'cauliflowers'},{'name':'salt'}],
        }
        
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user = self.user).all()
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exits = Ingredient.objects.filter(
                user = self.user,
                name = ingredient['name']
            ).exists()
            self.assertTrue(exit)
    
    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient. """
        ingredient = Ingredient.objects.create(user=self.user, name='lemon')
        payload = {
            'title':'Vietnames soup',
            'time_minutes':45,
            'price':'89',
            'ingredients':[{'name':'lemon'}, {'name':'fish sauce'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exist = recipe.ingredients.filter(
                name= ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exist)
    
    def test_create_ingredient_on_update(self):
        """test creating an ingredient when updating recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients':[{'name':'limes'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user = self.user, name = 'limes')
        recipe.refresh_from_db()
        self.assertIn(new_ingredient, recipe.ingredients.all())
        
    def test_update_recipe_assign_ingredient(self):
        """Test assiging an existing ingredient when updating recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='limon')
        recipe = create_recipe(user= self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='pepper')
        payload = {'ingredients':[{'name':'pepper'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe ingredients. """
        ingredient = Ingredient.objects.create(user=self.user, name='Cinnamon')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients':[]}
        url= detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags. """
        r1 = create_recipe(user=self.user, title='thai')
        r2 = create_recipe(user=self.user, title='ghomerh')
        tag1 = Tag.objects.create(user=self.user, name='vegan')
        tag2 = Tag.objects.create(user=self.user, name='vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='morgh')
        params = {'tags':f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data )
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)
    
    def test_filter_by_ingredients(self):
        """Test filtering recipe by ingredients. """
        r1 = create_recipe(user=self.user, title='chicken with cheese')
        r2 = create_recipe(user=self.user, title='pasta')
        ing1 = Ingredient.objects.create(user=self.user, name='peper')
        ing2 = Ingredient.objects.create(user=self.user, name='Parmesan cheese')
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        r3 = create_recipe(user=self.user, title='chicken barbecue')
        params = {'ingredients':f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPE_URL, params)
        
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data )
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTest(TestCase):
    """Tests for the image upload API."""
        
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='example@gmail.com', password='pas123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to recipe."""
        url = image_uploads_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image':image_file}
            res =self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image' , res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))
    
    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_uploads_url(self.recipe.id)
        payload = {'image':'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        



