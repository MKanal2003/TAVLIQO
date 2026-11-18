from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_RESTAURANT_ADMIN = 'restaurant_admin'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, 'Super Admin'),
        (ROLE_RESTAURANT_ADMIN, 'Restaurant Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_RESTAURANT_ADMIN
    )
    phone = models.CharField(max_length=20, blank=True)

    def is_superadmin(self):
        return self.role == self.ROLE_SUPERADMIN

    def is_restaurant_admin(self):
        return self.role == self.ROLE_RESTAURANT_ADMIN

    def __str__(self):
        return f"{self.email} [{self.get_role_display()}]"

class StaffUser(models.Model):
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='staff_members')
    name = models.CharField(max_length=100)
    pin = models.CharField(max_length=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"