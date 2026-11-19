from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order

class Command(BaseCommand):
    help = 'Deletes orders older than 1 year to keep the database clean while preserving analytics.'

    def handle(self, *args, **kwargs):
        # BUG FIX: Changed from 7 days to 365 days to preserve monthly/yearly stats
        one_year_ago = timezone.now() - timedelta(days=365)
        old_orders = Order.objects.filter(created_at__lt=one_year_ago)
        count = old_orders.count()
        old_orders.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old orders.'))