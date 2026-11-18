from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order

class Command(BaseCommand):
    help = 'Deletes orders older than 7 days to keep the database clean.'

    def handle(self, *args, **kwargs):
        seven_days_ago = timezone.now() - timedelta(days=7)
        old_orders = Order.objects.filter(created_at__lt=seven_days_ago)
        count = old_orders.count()
        old_orders.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old orders.'))