"""
Tests for the tag API.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe,
)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
     """create url for get specific tag with id"""
     return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email = 'user@example.com', password='testpass123'):
    """Create and return a user for test"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
     """Test Authenticated API request. """

     def setUp(self):
          self.client = APIClient()

     def test_auth_required(self):
          res = self.client.get(TAGS_URL)
          
          self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsAPITest(TestCase):
     """Test authenticated API request. """
     def setUp(self):
          self.client = APIClient()
          self.user = create_user(email='user@example.com', password='testpass123')
          self.client.force_authenticate(user=self.user)
     
     def test_retrive_tags(self):
          Tag.objects.create(user=self.user, name='vegan')
          Tag.objects.create(user=self.user, name='vegetarian')

          res = self.client.get(TAGS_URL)

          tags = Tag.objects.all().order_by('-name')
          serializer = TagSerializer(tags, many=True)
          self.assertEqual(res.status_code, status.HTTP_200_OK)
          self.assertEqual(res.data, serializer.data)
     
     def test_tags_limited_to_user(self):
          """Test list of tags is limited to authenticated user. """
          user2 = create_user(email='user2@example.com', password='testpass123')

          Tag.objects.create(user=user2, name='fruty')
          tag = Tag.objects.create(user= self.user, name='comfort foot')
          
          res = self.client.get(TAGS_URL)

          self.assertEqual(res.status_code, status.HTTP_200_OK)
          self.assertEqual(len(res.data), 1)
          self.assertEqual(res.data[0]['name'], tag.name)
          self.assertEqual(res.data[0]['id'], tag.id)

     def test_update_tag(self):
          tag = Tag.objects.create(user = self.user, name = 'after dinner')
          
          payload = {
               'name':'Dessert',
          }
          url = detail_url(tag.id)
          res = self.client.patch(url, payload)

          self.assertEqual(res.status_code, status.HTTP_200_OK)
          tag.refresh_from_db()
          self.assertEqual(tag.name , payload['name'])
     
     def test_delete_tag(self):
          """test deleting tag successful"""

          tag = Tag.objects.create(user=self.user, name='breakfast')

          url = detail_url(tag.id)
          res = self.client.delete(url)
          
          self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
          tags = Tag.objects.filter(user=self.user, name='breakfast')
          self.assertFalse(tags.exists())

     def test_filter_tags_assingned_to_recipes(self):
          """Test listing tags by those assigned to recipe"""
          t1 = Tag.objects.create(user=self.user, name='Appetizer')
          t2 = Tag.objects.create(user=self.user, name='Dessert')
          recipe = Recipe.objects.create(
               user=self.user, 
               title='Milk Soup',
               price=Decimal('4.00'),
               time_minutes=60,
          )
          recipe.tags.add(t1)

          res = self.client.get(TAGS_URL, {'assigned_only':1})
          s1 = TagSerializer(t1)
          s2 = TagSerializer(t2)

          self.assertIn(s1.data, res.data)
          self.assertNotIn(s2.data, res.data)
     
     def test_filter_tags_unique(self):
         tag = Tag.objects.create(user=self.user, name='Dinner')
         Tag.objects.create(user=self.user, name='Lunch')
         recipe1 = Recipe.objects.create(
              user=self.user,
              title='Pancakes',
              price=Decimal('10'),
              time_minutes=50,
         )
         recipe2 = Recipe.objects.create(
              user=self.user,
              title='Fried Fish',
              price=Decimal('80'),
              time_minutes=60,
         )
         recipe1.tags.add(tag)
         recipe2.tags.add(tag)

         res = self.client.get(TAGS_URL, {'assigned_only':1})
         
         self.assertEqual(len(res.data), 1)
         
