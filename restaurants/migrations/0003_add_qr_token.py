import secrets
from django.db import migrations, models
import restaurants.models


def _generate():
    return secrets.token_urlsafe(32)


def backfill_tokens(apps, schema_editor):
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    for r in Restaurant.objects.filter(qr_token__isnull=True):
        r.qr_token = _generate()
        r.save(update_fields=['qr_token'])


def reverse_backfill(apps, schema_editor):
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    Restaurant.objects.update(qr_token=None)


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0002_menuitem_is_vegetarian'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='qr_token',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.RunPython(backfill_tokens, reverse_backfill),
        migrations.AlterField(
            model_name='restaurant',
            name='qr_token',
            field=models.CharField(
                max_length=64,
                unique=True,
                db_index=True,
                default=restaurants.models.generate_qr_token,
                editable=False,
            ),
        ),
    ]