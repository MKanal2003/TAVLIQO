import secrets
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from accounts.models import User


def generate_qr_token():
    return secrets.token_urlsafe(32)


class Restaurant(models.Model):
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='restaurant'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=300)
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=generate_qr_token,
        editable=False,
    )
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    is_tax_enabled = models.BooleanField(default=False)
    cgst_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    sgst_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    
    is_online_payment_enabled = models.BooleanField(default=False)
    razorpay_key_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            if not base:
                base = 'restaurant'
            slug, n = base, 1
            while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_menu_url(self):
        return reverse('menu_by_token', kwargs={'token': self.qr_token})

    @property
    def total_items(self):
        return self.menu_items.count()

    @property
    def available_items_count(self):
        return self.menu_items.filter(is_available=True).count()

    @property
    def sold_out_count(self):
        return self.menu_items.filter(is_available=False).count()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Category(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"

    @property
    def item_count(self):
        return self.items.count()


class MenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'category__name', 'name']

    def __str__(self):
        return f"{self.name} (₹{self.price}) — {self.restaurant.name}"