"""Data migration (D2): rename the credit wire purpose ``ai_credits`` -> ``credits``
on existing rows, matching the code rename in credits/billing.py. Covers the grant
ledger (StripePayment.purpose) and the invoice records (Invoice.purpose)."""
from django.db import migrations


def _rename(apps, old, new):
    StripePayment = apps.get_model('stripe_payment', 'StripePayment')
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    StripePayment.objects.filter(purpose=old).update(purpose=new)
    Invoice.objects.filter(purpose=old).update(purpose=new)


def forwards(apps, schema_editor):
    _rename(apps, 'ai_credits', 'credits')


def backwards(apps, schema_editor):
    _rename(apps, 'credits', 'ai_credits')


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_payment', '0003_decouple_invoice'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
