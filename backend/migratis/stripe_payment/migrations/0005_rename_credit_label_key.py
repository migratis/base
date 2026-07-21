"""Data migration (P6): de-AI the credit invoice display key. Existing credit
invoices carry ``label_key='ai-credits'`` (the i18n key rendered in the billing
history); the key is renamed to ``credits`` in the same release as the code
rename in credits/billing.py and the i18n seed."""
from django.db import migrations


def forwards(apps, schema_editor):
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    Invoice.objects.filter(purpose='credits', label_key='ai-credits').update(label_key='credits')


def backwards(apps, schema_editor):
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    Invoice.objects.filter(purpose='credits', label_key='credits').update(label_key='ai-credits')


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_payment', '0004_rename_ai_credits_purpose_to_credits'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
