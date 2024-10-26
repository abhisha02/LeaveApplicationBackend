from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager,Group, Permission
from django.utils import timezone
from django.conf import settings
from hashlib import sha256
# Create your models here.
class CustomerManager(BaseUserManager):
    def create_user(self, email,  password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,  **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,  password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
       

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email,  password, **extra_fields)
    
class Employee(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    is_email_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False) 
    is_manager=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    profile= models.ImageField(upload_to='user/profile_pic/',null=True,blank=True)
    date_created = models.DateTimeField(default=timezone.now) 
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    username=None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [ 'first_name', 'last_name']
    objects = CustomerManager()
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
