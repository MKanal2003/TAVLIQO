import secrets
from django.db import models

def generate_public_token():
    return secrets.token_urlsafe(16)

class Customer(models.Model):
    restaurant_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING_ACCEPTANCE', 'Pending acceptance'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('SERVED', 'Served'),
        ('PAID', 'Paid'),
        ('CLOSED', 'Closed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    PAYMENT_INTENT_CHOICES = [('CASH', 'Cash'), ('ONLINE', 'Online')]

    public_token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_public_token)
    restaurant_id = models.IntegerField(db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    table_label = models.CharField(max_length=50, help_text="e.g. Table 5, Takeaway, Car 3")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_ACCEPTANCE', db_index=True)
    payment_intent = models.CharField(max_length=10, choices=PAYMENT_INTENT_CHOICES, default='CASH')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    rejection_reason = models.CharField(max_length=200, blank=True)
    
    notes = models.TextField(blank=True, help_text="e.g. Less spicy, No onion")
    
    staff_id = models.IntegerField(null=True, blank=True)
    staff_name = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item_id = models.IntegerField(db_index=True)
    name_snapshot = models.CharField(max_length=255)
    price_snapshot = models.DecimalField(max_digits=8, decimal_places=2)
    qty = models.PositiveIntegerField()

    @property
    def line_total(self):
        return self.price_snapshot * self.qty

class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_events')
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    actor_type = models.CharField(max_length=20)
    actor_id = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ConsentLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='consents')
    terms_version = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)

ALLOWED_TRANSITIONS = {
    'PENDING_ACCEPTANCE': {'CONFIRMED', 'REJECTED', 'CANCELLED', 'EXPIRED'},
    'CONFIRMED': {'PREPARING', 'CANCELLED'},
    'PREPARING': {'SERVED', 'CANCELLED'},
    'SERVED': {'PAID'},
    'PAID': {'CLOSED'},
}

NEXT_STATE = {
    'CONFIRMED': 'PREPARING',
    'PREPARING': 'SERVED',
    'SERVED': 'PAID',
}