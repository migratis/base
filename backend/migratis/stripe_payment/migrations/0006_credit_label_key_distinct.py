"""Data migration: give the credit-purchase invoice line a label_key distinct
from the shared ``credits`` i18n key.

i18n keys are global (one TranslationKey → one text, linked to many namespaces),
so ``credits`` cannot mean both 'Credit purchase' (billing/invoice) and
'Credits available: {{remaining}}' (credits balance widget). Existing credit
invoices carry ``label_key='credits'`` and therefore rendered the interpolated
balance template on the billing history; move them to ``credits-purchase`` to
match credits/billing.py and the i18n seed."""
from django.db import migrations


def forwards(apps, schema_editor):
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    Invoice.objects.filter(purpose='credits', label_key='credits').update(label_key='credits-purchase')


def backwards(apps, schema_editor):
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    Invoice.objects.filter(purpose='credits', label_key='credits-purchase').update(label_key='credits')


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_payment', '0005_rename_credit_label_key'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
