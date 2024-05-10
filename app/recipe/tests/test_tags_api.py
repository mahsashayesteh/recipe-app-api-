"""
Tests for the tag API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
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







