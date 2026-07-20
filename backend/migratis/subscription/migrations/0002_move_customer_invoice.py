"""Phase 5 — companion to stripe_payment.0002 (base lineage): drop
Customer/Invoice from the subscription app's state (tables stay; stripe_payment
now owns them) and repoint Subscription.customer. State-only — no DB changes.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0001_initial'),
        ('stripe_payment', '0002_customer_invoice'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='subscription',
                    name='customer',
                    field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='stripe_payment.customer'),
                ),
                migrations.DeleteModel(name='Invoice'),
                migrations.DeleteModel(name='Customer'),
            ],
            database_operations=[],
        ),
    ]
