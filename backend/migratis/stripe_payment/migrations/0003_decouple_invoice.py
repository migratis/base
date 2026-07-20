"""Decouple Invoice from the subscription domain so stripe_payment can be
installed standalone (payments without the subscription module).

Adds soft fields (``reference``, ``label_key``), denormalizes the existing
subscription/plan linkage into them, then drops the subscription/plan FKs.
"""
from django.db import migrations, models


def denormalize(apps, schema_editor):
    Invoice = apps.get_model('stripe_payment', 'Invoice')
    for inv in Invoice.objects.all().iterator():
        changed = False
        if inv.subscription_id:
            ref = getattr(inv.subscription, 'stripe_id', '') or ''
            if ref:
                inv.reference = ref
                changed = True
        if inv.plan_id:
            try:
                key = inv.plan.label.key
            except Exception:
                key = ''
            if key:
                inv.label_key = key
                changed = True
        if changed:
            inv.save(update_fields=['reference', 'label_key'])


class Migration(migrations.Migration):

    dependencies = [
        ('stripe_payment', '0002_customer_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='reference',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='invoice',
            name='label_key',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.RunPython(denormalize, migrations.RunPython.noop),
        migrations.RemoveField(model_name='invoice', name='subscription'),
        migrations.RemoveField(model_name='invoice', name='plan'),
    ]
