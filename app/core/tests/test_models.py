"""
Tests for models.
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(email='test@example.com', password='testpass123'):
    """create and return a new user"""
    return get_user_model().objects.create_user(email, password)

class ModelTests(TestCase):
    """Test models. """

    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
    
    def test_new_user_email_normalized(self):
        simple_emails=[
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@Example.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in simple_emails:
            user = get_user_model().objects.create_user(email, 'simple123')
            self.assertEqual(user.email, expected)
    
    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a valueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='test123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_create_recipe(self):
        """Test creating a recipe is successful. """
        user = get_user_model().objects.create_user(
            "test@example.com",
            "testpass123",
        )

        recipe = models.Recipe.objects.create(
             user = user,
             title = "sample test",
             time_minutes = 5,
             description = 'sample description',
             price = Decimal('5.5')
        )

        self.assertEqual(str(recipe), recipe.title)
    
    def test_creating_tag(self):
        """Test creating a tag is successful. """
        user = create_user()

        tag = models.Tag.objects.create(name='Tag1', user=user)

        self.assertEqual(tag.user, user)
        self.assertEqual(tag.name, str(tag))
    
    def test_create_ingrendient(self):
        """Test creating an ingrendient is successful. """

        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name= 'Ingrendient'
        )
        self.assertEqual(str(ingredient), ingredient.name)
