from django.db import models
from django.contrib.auth.models import AbstractBaseUser , BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify 
from django.utils import timezone
import uuid
import re


class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, password=None):
        if not email:
            raise ValueError("User must have an email address")

        # Clean and format the first and last names
        first_name_clean = re.sub(r"[^a-zA-Z]", "", first_name).lower()
        last_name_clean = re.sub(r"[^a-zA-Z]", "", last_name).lower()

        # Generate a base username (e.g., firstname.lastname)
        base_username = f"{first_name_clean}_{last_name_clean}"

        # Ensure the username is not too long
        max_username_length = 30
        if len(base_username) > max_username_length:
            base_username = base_username[:max_username_length]

        # Ensure username is unique
        username = base_username
        while User.objects.filter(username=username).exists():
            # Append a short random string for uniqueness
            random_string = uuid.uuid4().hex[:6]  # Take first 6 characters of a UUID
            username = f"{base_username}@{random_string}"

            # Ensure the username doesn't exceed the maximum length
            if len(username) > max_username_length:
                username = username[:max_username_length]

        user = self.model(
            email=self.normalize_email(email),
            username=username,  # Auto-generated username
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.is_active = False
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, password):
        user = self.create_user(first_name, last_name, email, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    username        = models.CharField(max_length=50, unique=True)
    email           = models.EmailField(max_length=100, unique=True)
    
    # required
    date_joined     = models.DateTimeField(auto_now_add=True)
    last_login      = models.DateTimeField(auto_now_add=True)
    is_admin        = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=False)
    is_superadmin   = models.BooleanField(default=False)
    otp             = models.CharField(max_length=6, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='users/profile_pictures/', blank=True, null=True)
    cover_picture = models.ImageField(upload_to='users/cover_pictures/', blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=50,null=True, blank=True)
    created_at = models.DateTimeField("created_at", default=timezone.now)
    updated_at = models.DateTimeField( auto_now=True)

    def get_profile_picture(self):
        if self.profile_picture:
            print("yes")
            return self.profile_picture.url
        return '/static/default_images/default_profile_picture.jpg'
    
    def get_cover_picture(self):
        if self.cover_picture:
            return self.cover_picture.url
        return '/static/default_images/default_profile_picture.jpg'
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def full_address(self):
        return f"{self.country} | {self.city}"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
