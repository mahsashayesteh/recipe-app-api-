"""
Database model.

"""
from  django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_feilds):
       """create, save and return a new user"""
       if not email:
           raise ValueError('کاربر باید ایمیل داشته باشد.')
       user = self.model(email=self.normalize_email(email), **extra_feilds)
       user.set_password(password)
       user.save(using= self._db)

       return user
    

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    """for login in django admin"""
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    def __str__(self):
        return self.email
    
    
class Recipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits = 5, decimal_places= 2)
    time_minutes = models.IntegerField()
    link = models.CharField(max_length = 255, blank= True)
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient')

    def __str__(self):
        return self.title
    
class Tag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete =models.CASCADE,
    )
    name = models.CharField(max_length = 255, blank=False)

    def __str__(self) :
        return self.name
    
class Ingredient(models.Model):
    """Ingredients for recipe"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
    )

    def __str__(self):
        return self.name
    